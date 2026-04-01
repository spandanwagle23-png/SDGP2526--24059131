import customtkinter as ctk
from views.base_dashboard import BaseDashboard
from controllers.tenant_controller import TenantController
from controllers.apartment_controller import ApartmentController
from controllers.maintenance_controller import MaintenanceController
from controllers.complaint_controller import ComplaintController
from controllers.auth_controller import AuthController
from controllers.user_controller import UserController
from models.complaint_model import COMPLAINT_TYPES
from models.maintenance_model import PRIORITY_LEVELS
from datetime import datetime, timedelta

class FrontdeskDashboard(BaseDashboard):
    def __init__(self, master, user):
        nav = [
            ("Dashboard",    "📊", self._show_dashboard),
            ("Register Tenant","👤", self._show_register_tenant),
            ("Tenant Lookup", "🔍", self._show_lookup),
            ("Assign Apt",   "🏠", self._show_assign),
            ("Maintenance",  "🔧", self._show_maintenance),
            ("Complaints",   "📝", self._show_complaints),            ("Settings",    "⚙️", self._show_settings),        ]
        super().__init__(master, user, nav)
        self.ten_ctrl   = TenantController()
        self.apt_ctrl   = ApartmentController()
        self.maint_ctrl = MaintenanceController()
        self.comp_ctrl  = ComplaintController()
        self.auth       = AuthController()
        self.user_ctrl  = UserController()
        self.location   = user.get("location")
        self.navigate_to("Dashboard")

    def _show_dashboard(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Front Desk Overview", f"Location: {self.location}")

        tenants = self.ten_ctrl.get_all_tenants(self.location, "active")
        apts    = self.apt_ctrl.get_all_apartments(self.location)
        maint   = self.maint_ctrl.get_all_requests(location=self.location)
        open_m  = [r for r in maint if r["status"] != "resolved"]
        comps   = self.comp_ctrl.get_all_complaints(location=self.location, status="open")

        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", pady=(0,16))
        for t, v, s, c in [
            ("Active Tenants", len(tenants), "", "#68d391"),
            ("Total Apartments", len(apts), "", "#4e9af1"),
            ("Open Maintenance", len(open_m), "Requires attention", "#f6ad55"),
            ("Open Complaints", len(comps), "Requires review", "#fc8181"),
        ]:
            card = self.stat_card(row, t, v, s, c)
            card.pack(side="left", fill="both", expand=True, padx=4)

        # Recent tenants
        card = self.make_card(f, "Recently Registered Tenants")
        card.pack(fill="x", pady=(0,12))
        recent = sorted(tenants, key=lambda x: x.get("created_at", datetime.min), reverse=True)[:5]
        rows = [(t["full_name"], t["ni_number"], t["email"], t["phone"], t["location"]) for t in recent]
        if rows:
            self.make_table(card, ["Name","NI","Email","Phone","Location"],
                            rows, [160,110,200,120,100]).pack(fill="x", padx=12, pady=(0,12))
        else:
            ctk.CTkLabel(card, text="No tenants registered yet.", text_color="#94a3b8",
                         font=("Helvetica",12)).pack(padx=16, pady=12)

    def _show_register_tenant(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Register New Tenant")

        card = self.make_card(f)
        card.pack(fill="x")

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=12)

        def row_input(r, label, ph, col=0, show=""):
            ctk.CTkLabel(form, text=label, font=("Helvetica",12), text_color="#94a3b8",
                         anchor="w").grid(row=r, column=col*2, sticky="w", padx=(0,8), pady=4)
            e = ctk.CTkEntry(form, width=240, placeholder_text=ph, show=show)
            e.grid(row=r, column=col*2+1, sticky="ew", padx=(0,20), pady=4)
            return e

        ni_e    = row_input(0,"NI Number *","e.g. AB123456C", 0)
        name_e  = row_input(0,"Full Name *","Full legal name", 1)
        phone_e = row_input(1,"Phone *","07xxx xxxxxx", 0)
        email_e = row_input(1,"Email *","email@example.com", 1)
        occ_e   = row_input(2,"Occupation *","Job title", 0)
        ref_e   = row_input(2,"References","Referee name/contact", 1)
        dob_e   = row_input(3,"Date of Birth","YYYY-MM-DD", 0)
        emerg_e = row_input(3,"Emergency Contact","Phone number", 1)
        lease_e = row_input(4,"Lease Period (months) *","e.g. 12", 0)
        apt_req = row_input(4,"Apt Requirements","e.g. 2-Bedroom", 1)

        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        msg = ctk.CTkLabel(card, text="", font=("Helvetica",12), text_color="#fc8181")
        msg.pack()

        def submit():
            from utils.validators import validate_email, validate_phone, validate_ni_number
            ni    = ni_e.get().strip().upper()
            name  = name_e.get().strip()
            phone = phone_e.get().strip()
            email = email_e.get().strip()
            occ   = occ_e.get().strip()
            ref   = ref_e.get().strip()
            dob   = dob_e.get().strip()
            emerg = emerg_e.get().strip()
            req   = apt_req.get().strip()
            try:
                lease = int(lease_e.get())
            except ValueError:
                msg.configure(text="Lease period must be a number.", text_color="#fc8181"); return

            if not all([ni, name, phone, email, occ]):
                msg.configure(text="Please fill all required (*) fields.", text_color="#fc8181"); return
            if not validate_ni_number(ni):
                msg.configure(text="Invalid NI number format (e.g. AB123456C).", text_color="#fc8181"); return
            if not validate_email(email):
                msg.configure(text="Invalid email address.", text_color="#fc8181"); return
            if not validate_phone(phone):
                msg.configure(text="Invalid phone number.", text_color="#fc8181"); return

            tid, username, password, err = self.ten_ctrl.register_tenant(
                ni, name, phone, email, occ, ref, req, lease, dob, emerg,
                self.location, self.user["username"]
            )
            if err:
                msg.configure(text=err, text_color="#fc8181")
            else:
                credentials_msg = f"✓ Tenant registered! Login: {username} | Password: {password}"
                msg.configure(text=credentials_msg, text_color="#68d391")
                for e in [ni_e,name_e,phone_e,email_e,occ_e,ref_e,dob_e,emerg_e,lease_e,apt_req]:
                    e.delete(0,"end")

        ctk.CTkButton(card, text="Register Tenant", fg_color="#4e9af1", hover_color="#2b6cb0",
                      height=42, font=("Helvetica",13,"bold"), command=submit
                      ).pack(padx=20, pady=12, fill="x")

    def _show_lookup(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Tenant Lookup", "Search and manage tenant records")

        search_row = ctk.CTkFrame(f, fg_color="transparent")
        search_row.pack(fill="x", pady=(0,12))
        search_e = ctk.CTkEntry(search_row, placeholder_text="Search by name, email, NI or phone...",
                                width=380, height=40)
        search_e.pack(side="left", padx=(0,8))
        results_frame = ctk.CTkFrame(f, fg_color="transparent")
        results_frame.pack(fill="both", expand=True)

        def do_search():
            for w in results_frame.winfo_children():
                w.destroy()
            q = search_e.get().strip()
            tenants = self.ten_ctrl.search_tenants(q, self.location) if q else self.ten_ctrl.get_all_tenants(self.location)
            if not tenants:
                ctk.CTkLabel(results_frame, text="No tenants found.", text_color="#94a3b8",
                             font=("Helvetica",12)).pack(pady=20)
                return
            for t in tenants:
                tc = ctk.CTkFrame(results_frame, fg_color="#1c2333", corner_radius=10)
                tc.pack(fill="x", pady=4)
                top = ctk.CTkFrame(tc, fg_color="transparent")
                top.pack(fill="x", padx=14, pady=(10,4))
                ctk.CTkLabel(top, text=t["full_name"], font=("Helvetica",14,"bold"),
                             text_color="white").pack(side="left")
                status_col = "#68d391" if t.get("status")=="active" else "#fc8181"
                ctk.CTkLabel(top, text=t.get("status","").upper(), font=("Helvetica",10),
                             text_color=status_col).pack(side="right")
                info = ctk.CTkFrame(tc, fg_color="transparent")
                info.pack(fill="x", padx=14, pady=(0,10))
                for label, val in [("NI",t["ni_number"]),("Email",t["email"]),
                                   ("Phone",t["phone"]),("Occupation",t.get("occupation",""))]:
                    ctk.CTkLabel(info, text=f"{label}: {val}", font=("Helvetica",11),
                                 text_color="#94a3b8").pack(side="left", padx=(0,16))
                btn_row = ctk.CTkFrame(tc, fg_color="transparent")
                btn_row.pack(fill="x", padx=14, pady=(0,10))
                ctk.CTkButton(btn_row, text="Edit", width=80, height=30, fg_color="#2d3748",
                              command=lambda tid=str(t["_id"]), tn=t["full_name"]: self._edit_tenant(tid, tn)
                              ).pack(side="left", padx=(0,6))
                if t.get("status") == "active":
                    ctk.CTkButton(btn_row, text="Early Termination", width=140, height=30,
                                  fg_color="#7c3a3a", hover_color="#992222",
                                  command=lambda tid=str(t["_id"]): self._early_term(tid)
                                  ).pack(side="left")

        ctk.CTkButton(search_row, text="Search", fg_color="#4e9af1", height=40,
                      command=do_search).pack(side="left")
        search_e.bind("<Return>", lambda e: do_search())
        do_search()

    def _edit_tenant(self, tenant_id, name):
        dlg = ctk.CTkToplevel(self.content_area)
        dlg.title(f"Edit Tenant — {name}")
        dlg.geometry("420x320")
        dlg.grab_set()
        t = self.ten_ctrl.get_tenant_by_id(tenant_id)
        if not t:
            return

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=16)

        fields = {}
        for label, key in [("Phone","phone"),("Email","email"),("Occupation","occupation"),("Emergency Contact","emergency_contact")]:
            ctk.CTkLabel(form, text=label, font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
            e = ctk.CTkEntry(form)
            e.insert(0, t.get(key,""))
            e.pack(fill="x", pady=(2,8))
            fields[key] = e

        msg = ctk.CTkLabel(form, text="", font=("Helvetica",11), text_color="#fc8181")
        msg.pack()

        def save():
            updates = {k: v.get().strip() for k, v in fields.items()}
            ok, m = self.ten_ctrl.update_tenant(tenant_id, updates)
            msg.configure(text=m, text_color="#68d391" if ok else "#fc8181")
            if ok:
                dlg.after(1000, dlg.destroy)

        ctk.CTkButton(form, text="Save Changes", fg_color="#4e9af1", command=save).pack(fill="x", pady=4)

    def _early_term(self, tenant_id):
        penalty, err = self.ten_ctrl.request_early_termination(tenant_id, datetime.utcnow())
        if err:
            self.show_message(self.content_area, err, "#fc8181")
        else:
            self.show_message(self.content_area,
                              f"Early termination requested.\nPenalty: £{penalty:.2f} (5% of monthly rent)\n1 month notice period started.",
                              "#f6ad55")

    def _show_assign(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Assign Apartment to Tenant")

        card = self.make_card(f)
        card.pack(fill="x")
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=16)

        # Tenant select
        ctk.CTkLabel(form, text="Select Tenant *", font=("Helvetica",12), text_color="#94a3b8").grid(row=0,column=0,sticky="w",pady=4)
        tenants = self.ten_ctrl.get_all_tenants(self.location, "active")
        tenant_opts = [f"{t['full_name']} ({t['ni_number']})" for t in tenants]
        tenant_map = {f"{t['full_name']} ({t['ni_number']})": t for t in tenants}
        t_var = ctk.StringVar(value=tenant_opts[0] if tenant_opts else "No tenants")
        ctk.CTkOptionMenu(form, values=tenant_opts or ["No tenants"], variable=t_var,
                          fg_color="#1c2333", button_color="#4e9af1", width=280).grid(row=0,column=1,sticky="ew",padx=8,pady=4)

        # Apartment select
        ctk.CTkLabel(form, text="Select Apartment *", font=("Helvetica",12), text_color="#94a3b8").grid(row=1,column=0,sticky="w",pady=4)
        apts = self.apt_ctrl.get_all_apartments(self.location, "available")
        apt_opts = [f"{a['apartment_number']} — {a['apartment_type']} — £{a['monthly_rent']}/mo" for a in apts]
        apt_map = {f"{a['apartment_number']} — {a['apartment_type']} — £{a['monthly_rent']}/mo": a for a in apts}
        a_var = ctk.StringVar(value=apt_opts[0] if apt_opts else "No available apartments")
        ctk.CTkOptionMenu(form, values=apt_opts or ["None"], variable=a_var,
                          fg_color="#1c2333", button_color="#4e9af1", width=320).grid(row=1,column=1,sticky="ew",padx=8,pady=4)

        ctk.CTkLabel(form, text="Start Date *", font=("Helvetica",12), text_color="#94a3b8").grid(row=2,column=0,sticky="w",pady=4)
        start_e = ctk.CTkEntry(form, placeholder_text="YYYY-MM-DD")
        start_e.insert(0, datetime.utcnow().strftime("%Y-%m-%d"))
        start_e.grid(row=2,column=1,sticky="ew",padx=8,pady=4)

        ctk.CTkLabel(form, text="End Date *", font=("Helvetica",12), text_color="#94a3b8").grid(row=3,column=0,sticky="w",pady=4)
        end_e = ctk.CTkEntry(form, placeholder_text="YYYY-MM-DD")
        end_e.insert(0, (datetime.utcnow()+timedelta(days=365)).strftime("%Y-%m-%d"))
        end_e.grid(row=3,column=1,sticky="ew",padx=8,pady=4)

        ctk.CTkLabel(form, text="Deposit (£) *", font=("Helvetica",12), text_color="#94a3b8").grid(row=4,column=0,sticky="w",pady=4)
        dep_e = ctk.CTkEntry(form, placeholder_text="e.g. 1900")
        dep_e.grid(row=4,column=1,sticky="ew",padx=8,pady=4)
        form.columnconfigure(1, weight=1)

        msg = ctk.CTkLabel(card, text="", font=("Helvetica",12), text_color="#fc8181")
        msg.pack()

        def assign():
            from utils.validators import validate_date_format
            sel_t = t_var.get()
            sel_a = a_var.get()
            if sel_t not in tenant_map or sel_a not in apt_map:
                msg.configure(text="Please select valid tenant and apartment.", text_color="#fc8181"); return
            t_obj = tenant_map[sel_t]
            a_obj = apt_map[sel_a]
            start_s = start_e.get().strip()
            end_s   = end_e.get().strip()
            if not validate_date_format(start_s) or not validate_date_format(end_s):
                msg.configure(text="Invalid date format. Use YYYY-MM-DD.", text_color="#fc8181"); return
            try:
                dep = float(dep_e.get())
            except ValueError:
                msg.configure(text="Deposit must be a number.", text_color="#fc8181"); return
            start_dt = datetime.strptime(start_s, "%Y-%m-%d")
            end_dt   = datetime.strptime(end_s, "%Y-%m-%d")
            lease_id, err = self.apt_ctrl.assign_tenant(
                str(a_obj["_id"]), str(t_obj["_id"]), t_obj["full_name"],
                start_dt, end_dt, a_obj["monthly_rent"], dep, self.user["username"]
            )
            if err:
                msg.configure(text=err, text_color="#fc8181")
            else:
                msg.configure(text=f"Apartment assigned! Lease ID: {lease_id}", text_color="#68d391")

        ctk.CTkButton(card, text="Assign Apartment", fg_color="#4e9af1", hover_color="#2b6cb0",
                      height=42, command=assign).pack(padx=20, pady=(4,16), fill="x")

    def _show_maintenance(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Maintenance Requests", "Log and track maintenance issues")

        # Log new
        top = ctk.CTkButton(f, text="+ Log New Request", fg_color="#4e9af1", hover_color="#2b6cb0",
                            command=lambda: self._log_maint_dialog())
        top.pack(anchor="e", pady=(0,12))

        reqs = self.maint_ctrl.get_all_requests(location=self.location)
        status_icon = {"submitted":"🔵","investigating":"🟡","scheduled":"🟠","in_progress":"🔄","resolved":"✅","cancelled":"❌"}
        rows = [(r["apartment_number"], r["issue_title"], r["priority"],
                 status_icon.get(r["status"],"")+" "+r["status"], r["tenant_name"],
                 r["created_at"].strftime("%d/%m/%Y") if isinstance(r.get("created_at"),datetime) else "")
                for r in reqs]
        tbl = self.make_table(f, ["Apt #","Issue","Priority","Status","Tenant","Date"],
                              rows, [80,180,80,130,140,90])
        tbl.pack(fill="both", expand=True)

    def _log_maint_dialog(self):
        dlg = ctk.CTkToplevel(self.content_area)
        dlg.title("Log Maintenance Request")
        dlg.geometry("480x460")
        dlg.grab_set()

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(form, text="Log Maintenance Request", font=("Helvetica",15,"bold"),
                     text_color="white").pack(anchor="w", pady=(0,12))

        tenants = self.ten_ctrl.get_all_tenants(self.location, "active")
        t_opts = [f"{t['full_name']}" for t in tenants]
        t_map  = {t["full_name"]: t for t in tenants}
        ctk.CTkLabel(form, text="Tenant", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        t_var = ctk.StringVar(value=t_opts[0] if t_opts else "")
        ctk.CTkOptionMenu(form, values=t_opts or ["None"], variable=t_var,
                          fg_color="#1c2333", button_color="#4e9af1").pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Issue Title", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        title_e = ctk.CTkEntry(form, placeholder_text="Brief title of the issue")
        title_e.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Description", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        desc_e = ctk.CTkTextbox(form, height=80)
        desc_e.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Priority", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        pri_var = ctk.StringVar(value="Medium")
        ctk.CTkOptionMenu(form, values=PRIORITY_LEVELS, variable=pri_var,
                          fg_color="#1c2333", button_color="#4e9af1").pack(fill="x", pady=(2,10))

        msg = ctk.CTkLabel(form, text="", font=("Helvetica",11), text_color="#fc8181")
        msg.pack()

        def submit():
            tn = t_var.get()
            if tn not in t_map:
                msg.configure(text="Select a valid tenant."); return
            t_obj = t_map[tn]
            apt = self.apt_ctrl.get_all_apartments(self.location, "occupied")
            apt_obj = next((a for a in apt if a.get("current_tenant_id")==str(t_obj["_id"])), None)
            if not apt_obj:
                msg.configure(text="Tenant has no assigned apartment."); return
            ttl = title_e.get().strip()
            desc = desc_e.get("0.0","end").strip()
            if not ttl or not desc:
                msg.configure(text="Title and description required."); return
            _, err = self.maint_ctrl.submit_request(
                str(t_obj["_id"]), t_obj["full_name"], str(apt_obj["_id"]),
                apt_obj["apartment_number"], self.location, ttl, desc,
                pri_var.get(), self.user["username"]
            )
            if err:
                msg.configure(text=err, text_color="#fc8181")
            else:
                msg.configure(text="Maintenance request logged!", text_color="#68d391")
                dlg.after(1000, dlg.destroy)

        ctk.CTkButton(form, text="Submit Request", fg_color="#4e9af1", command=submit).pack(fill="x", pady=4)

    def _show_complaints(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Complaints", "Tenant complaints log")

        ctk.CTkButton(f, text="+ Log Complaint", fg_color="#4e9af1",
                      command=lambda: self._log_complaint_dialog()).pack(anchor="e", pady=(0,12))

        comps = self.comp_ctrl.get_all_complaints(location=self.location)
        rows = [(c["tenant_name"], c["complaint_type"], c["subject"],
                 c["status"], c["created_at"].strftime("%d/%m/%Y") if isinstance(c.get("created_at"),datetime) else "")
                for c in comps]
        tbl = self.make_table(f, ["Tenant","Type","Subject","Status","Date"],
                              rows, [160,100,220,100,90])
        tbl.pack(fill="both", expand=True)

    def _log_complaint_dialog(self):
        dlg = ctk.CTkToplevel(self.content_area)
        dlg.title("Log Complaint")
        dlg.geometry("480x430")
        dlg.grab_set()

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(form, text="Log Tenant Complaint", font=("Helvetica",15,"bold"),
                     text_color="white").pack(anchor="w", pady=(0,12))

        tenants = self.ten_ctrl.get_all_tenants(self.location, "active")
        t_opts = [t["full_name"] for t in tenants]
        t_map  = {t["full_name"]: t for t in tenants}
        ctk.CTkLabel(form, text="Tenant", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        t_var = ctk.StringVar(value=t_opts[0] if t_opts else "")
        ctk.CTkOptionMenu(form, values=t_opts or ["None"], variable=t_var,
                          fg_color="#1c2333", button_color="#4e9af1").pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Type", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        ct_var = ctk.StringVar(value=COMPLAINT_TYPES[0])
        ctk.CTkOptionMenu(form, values=COMPLAINT_TYPES, variable=ct_var,
                          fg_color="#1c2333", button_color="#4e9af1").pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Subject", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        subj_e = ctk.CTkEntry(form, placeholder_text="Brief subject")
        subj_e.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Description", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        desc_e = ctk.CTkTextbox(form, height=70)
        desc_e.pack(fill="x", pady=(2,10))

        msg = ctk.CTkLabel(form, text="", font=("Helvetica",11), text_color="#fc8181")
        msg.pack()

        def submit():
            tn = t_var.get()
            if tn not in t_map:
                msg.configure(text="Select valid tenant."); return
            t_obj = t_map[tn]
            apt_list = self.apt_ctrl.get_all_apartments(self.location, "occupied")
            apt_obj = next((a for a in apt_list if a.get("current_tenant_id")==str(t_obj["_id"])), None)
            if not apt_obj:
                msg.configure(text="Tenant has no assigned apartment."); return
            subj = subj_e.get().strip()
            desc = desc_e.get("0.0","end").strip()
            if not subj or not desc:
                msg.configure(text="Subject and description required."); return
            _, err = self.comp_ctrl.submit_complaint(
                str(t_obj["_id"]), t_obj["full_name"], str(apt_obj["_id"]),
                apt_obj["apartment_number"], self.location, ct_var.get(),
                subj, desc, self.user["username"]
            )
            if err:
                msg.configure(text=err, text_color="#fc8181")
            else:
                msg.configure(text="Complaint logged!", text_color="#68d391")
                dlg.after(1000, dlg.destroy)

        ctk.CTkButton(form, text="Submit Complaint", fg_color="#4e9af1", command=submit).pack(fill="x", pady=4)

    def _show_settings(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Settings", "Manage your account")

        # Profile Info Card
        card = self.make_card(f, "👤 Profile Information")
        card.pack(fill="x", pady=(0,16))
        
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=16, pady=12)
        
        for label, value in [
            ("Full Name", self.user.get("full_name", "N/A")),
            ("Username", self.user.get("username", "N/A")),
            ("Email", self.user.get("email", "N/A")),
            ("Location", self.user.get("location", "N/A")),
        ]:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=f"{label}:", font=("Helvetica",12,"bold"), 
                        text_color="#94a3b8").pack(side="left", padx=(0,20))
            ctk.CTkLabel(row, text=value, font=("Helvetica",12), 
                        text_color="white").pack(side="left")

        # Change Password Card
        card2 = self.make_card(f, "🔐 Change Password")
        card2.pack(fill="x")
        
        form = ctk.CTkFrame(card2, fg_color="transparent")
        form.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(form, text="Current Password *", font=("Helvetica",12), 
                    text_color="#94a3b8", anchor="w").pack(fill="x")
        current_pw = ctk.CTkEntry(form, placeholder_text="Enter current password", show="•")
        current_pw.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="New Password *", font=("Helvetica",12), 
                    text_color="#94a3b8", anchor="w").pack(fill="x")
        new_pw = ctk.CTkEntry(form, placeholder_text="Enter new password (min 8 chars)", show="•")
        new_pw.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Confirm New Password *", font=("Helvetica",12), 
                    text_color="#94a3b8", anchor="w").pack(fill="x")
        confirm_pw = ctk.CTkEntry(form, placeholder_text="Confirm new password", show="•")
        confirm_pw.pack(fill="x", pady=(2,10))

        msg = ctk.CTkLabel(form, text="", font=("Helvetica",11), text_color="#fc8181")
        msg.pack()

        def change_password():
            from utils.validators import validate_password
            current = current_pw.get()
            new = new_pw.get()
            confirm = confirm_pw.get()

            if not all([current, new, confirm]):
                msg.configure(text="All fields required.", text_color="#fc8181")
                return
            
            if new != confirm:
                msg.configure(text="New passwords do not match.", text_color="#fc8181")
                return
            
            ok, err = validate_password(new)
            if not ok:
                msg.configure(text=err, text_color="#fc8181")
                return

            success, error = self.user_ctrl.change_password(self.user["_id"], current, new)
            
            if success:
                msg.configure(text="✅ Password changed successfully!", text_color="#68d391")
                current_pw.delete(0, "end")
                new_pw.delete(0, "end")
                confirm_pw.delete(0, "end")
            else:
                msg.configure(text=error, text_color="#fc8181")

        ctk.CTkButton(form, text="Change Password", fg_color="#4e9af1", hover_color="#2b6cb0",
                     command=change_password).pack(fill="x", pady=8)
