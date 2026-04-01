import customtkinter as ctk
from views.base_dashboard import BaseDashboard
from controllers.maintenance_controller import MaintenanceController
from models.maintenance_model import PRIORITY_LEVELS, MAINTENANCE_STATUS
from datetime import datetime

class MaintenanceDashboard(BaseDashboard):
    def __init__(self, master, user):
        nav = [
            ("Dashboard",  "📊", self._show_dashboard),
            ("My Tasks",   "🔧", self._show_my_tasks),
            ("All Requests","📋", self._show_all_requests),
            ("Resolve",    "✅", self._show_resolve),
        ]
        super().__init__(master, user, nav)
        self.maint_ctrl = MaintenanceController()
        self.location   = user.get("location")
        self.navigate_to("Dashboard")

    def _show_dashboard(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Maintenance Dashboard", f"Location: {self.location}")

        all_req = self.maint_ctrl.get_all_requests(location=self.location)
        by_status = {}
        for r in all_req:
            s = r.get("status","unknown")
            by_status[s] = by_status.get(s,0) + 1

        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", pady=(0,16))
        for label, key, col in [
            ("Submitted",  "submitted",  "#4e9af1"),
            ("Scheduled",  "scheduled",  "#f6ad55"),
            ("In Progress","in_progress","#9f7aea"),
            ("Resolved",   "resolved",   "#68d391"),
        ]:
            c = self.stat_card(row, label, by_status.get(key,0), "", col)
            c.pack(side="left", fill="both", expand=True, padx=4)

        # High priority pending
        card = self.make_card(f, "🔴 High/Emergency Priority — Unresolved")
        card.pack(fill="x", pady=(0,12))
        high = [r for r in all_req if r.get("priority") in ["High","Emergency"]
                and r.get("status") not in ["resolved","cancelled"]]
        if high:
            rows = [(r["issue_title"], r["priority"], r["tenant_name"],
                     r["apartment_number"], r["status"],
                     r["created_at"].strftime("%d/%m/%Y") if isinstance(r.get("created_at"),datetime) else "")
                    for r in high]
            self.make_table(card, ["Issue","Priority","Tenant","Apt","Status","Date"],
                            rows, [200,80,140,80,110,90]).pack(fill="x", padx=12, pady=(0,12))
        else:
            ctk.CTkLabel(card, text="No high-priority issues pending.",
                         text_color="#68d391", font=("Helvetica",12)).pack(padx=16, pady=12)

    def _show_my_tasks(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "My Assigned Tasks")

        my_name = self.user.get("full_name","")
        tasks = [r for r in self.maint_ctrl.get_all_requests(location=self.location)
                 if r.get("assigned_to") == my_name and r.get("status") != "resolved"]

        if not tasks:
            ctk.CTkLabel(f, text="No tasks currently assigned to you.",
                         text_color="#94a3b8", font=("Helvetica",14)).pack(pady=40)
            return

        for r in tasks:
            card = ctk.CTkFrame(f, fg_color="#1c2333", corner_radius=10)
            card.pack(fill="x", pady=6)
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=14, pady=(12,4))
            ctk.CTkLabel(header, text=r["issue_title"], font=("Helvetica",14,"bold"),
                         text_color="white").pack(side="left")
            pri_col = {"High":"#fc8181","Emergency":"#ff4444","Medium":"#f6ad55","Low":"#68d391"}.get(r.get("priority",""),"white")
            ctk.CTkLabel(header, text=r.get("priority",""), font=("Helvetica",11),
                         text_color=pri_col).pack(side="right")
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(fill="x", padx=14, pady=(0,4))
            for label, val in [("Tenant",r["tenant_name"]),("Apt",r["apartment_number"]),
                               ("Status",r["status"]),("Scheduled",r.get("scheduled_date","Not set"))]:
                sval = val.strftime("%d/%m/%Y") if isinstance(val,datetime) else str(val)
                ctk.CTkLabel(info, text=f"{label}: {sval}", font=("Helvetica",11),
                             text_color="#94a3b8").pack(side="left", padx=(0,16))
            desc = r.get("issue_description","")
            ctk.CTkLabel(card, text=desc, font=("Helvetica",11), text_color="#718096",
                         wraplength=700, anchor="w").pack(fill="x", padx=14, pady=(0,8))

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=14, pady=(0,12))
            if r.get("status") == "scheduled":
                ctk.CTkButton(btn_row, text="Mark In Progress", width=140, height=30,
                              fg_color="#9f7aea", hover_color="#7c3aed",
                              command=lambda rid=str(r["_id"]): self._update_status(rid,"in_progress")
                              ).pack(side="left", padx=(0,6))
            ctk.CTkButton(btn_row, text="Resolve", width=100, height=30,
                          fg_color="#68d391", hover_color="#48bb78", text_color="black",
                          command=lambda rid=str(r["_id"]): self._resolve_dialog(rid)
                          ).pack(side="left")

    def _show_all_requests(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "All Maintenance Requests")

        # Filters
        top = ctk.CTkFrame(f, fg_color="transparent")
        top.pack(fill="x", pady=(0,12))
        status_var = ctk.StringVar(value="All")
        pri_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(top, values=["All"]+MAINTENANCE_STATUS, variable=status_var,
                          fg_color="#1c2333", button_color="#4e9af1",
                          command=lambda v: self._refresh_requests(f, status_var.get(), pri_var.get())
                          ).pack(side="left", padx=(0,8))
        ctk.CTkOptionMenu(top, values=["All"]+PRIORITY_LEVELS, variable=pri_var,
                          fg_color="#1c2333", button_color="#4e9af1",
                          command=lambda v: self._refresh_requests(f, status_var.get(), pri_var.get())
                          ).pack(side="left", padx=(0,8))
        ctk.CTkButton(top, text="Assign Selected", fg_color="#4e9af1",
                      command=lambda: self._assign_dialog(f)).pack(side="right")

        self._refresh_requests(f, "All", "All")

    def _refresh_requests(self, parent, status, priority):
        # Destroy existing table container if present
        if hasattr(parent, "_req_table_container"):
            if parent._req_table_container is not None and parent._req_table_container.winfo_exists():
                parent._req_table_container.destroy()
        
        s = None if status == "All" else status
        p = None if priority == "All" else priority
        reqs = self.maint_ctrl.get_all_requests(location=self.location, status=s, priority=p)
        rows = [(r["issue_title"][:40], r["priority"], r["tenant_name"], r["apartment_number"],
                 r["status"], r.get("assigned_to","Unassigned"),
                 r["created_at"].strftime("%d/%m/%Y") if isinstance(r.get("created_at"),datetime) else "")
                for r in reqs]
        
        # Create container for table with filter header
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True)
        parent._req_table_container = container
        
        # Show filter status
        filter_text = "Filters: "
        filters_applied = []
        if status != "All":
            filters_applied.append(f"Status: {status}")
        if priority != "All":
            filters_applied.append(f"Priority: {priority}")
        
        if filters_applied:
            filter_text += " | ".join(filters_applied)
            ctk.CTkLabel(container, text=filter_text, font=("Helvetica",11), 
                        text_color="#4e9af1").pack(fill="x", pady=(0,8))
        
        tbl = self.make_table(container, ["Issue","Priority","Tenant","Apt","Status","Assigned To","Date"],
                              rows, [180,80,130,70,120,130,90])
        tbl.pack(fill="both", expand=True)

    def _assign_dialog(self, parent):
        dlg = ctk.CTkToplevel(parent)
        dlg.title("Assign Maintenance Request")
        dlg.geometry("500x420")
        dlg.grab_set()

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(form, text="Assign Maintenance Request", font=("Helvetica",15,"bold"),
                     text_color="white").pack(anchor="w", pady=(0,12))

        # Get unassigned/submitted requests
        reqs = self.maint_ctrl.get_all_requests(location=self.location, status="submitted")
        req_opts = [f"{r['apartment_number']} — {r['issue_title'][:40]}" for r in reqs]
        req_map  = {f"{r['apartment_number']} — {r['issue_title'][:40]}": r for r in reqs}

        ctk.CTkLabel(form, text="Request", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        r_var = ctk.StringVar(value=req_opts[0] if req_opts else "No pending requests")
        ctk.CTkOptionMenu(form, values=req_opts or ["None"], variable=r_var,
                          fg_color="#1c2333", button_color="#4e9af1", width=420).pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Assign To (Worker Name)", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        worker_e = ctk.CTkEntry(form, placeholder_text="Worker full name")
        worker_e.insert(0, self.user.get("full_name",""))
        worker_e.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Scheduled Date (YYYY-MM-DD)", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        date_e = ctk.CTkEntry(form, placeholder_text="YYYY-MM-DD")
        date_e.insert(0, datetime.utcnow().strftime("%Y-%m-%d"))
        date_e.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Scheduled Time", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        time_e = ctk.CTkEntry(form, placeholder_text="e.g. 10:00 AM")
        time_e.insert(0, "10:00 AM")
        time_e.pack(fill="x", pady=(2,10))

        msg = ctk.CTkLabel(form, text="", font=("Helvetica",11), text_color="#fc8181")
        msg.pack()

        def submit():
            sel = r_var.get()
            if sel not in req_map:
                msg.configure(text="Select valid request."); return
            r_obj = req_map[sel]
            worker = worker_e.get().strip()
            date_s = date_e.get().strip()
            time_s = time_e.get().strip()
            if not worker or not date_s:
                msg.configure(text="Worker and date required."); return
            from utils.validators import validate_date_format
            if not validate_date_format(date_s):
                msg.configure(text="Invalid date format."); return
            sched_dt = datetime.strptime(date_s, "%Y-%m-%d")
            ok, m = self.maint_ctrl.assign_request(str(r_obj["_id"]), worker, sched_dt, time_s)
            msg.configure(text=m, text_color="#68d391" if ok else "#fc8181")
            if ok:
                dlg.after(1000, dlg.destroy)

        ctk.CTkButton(form, text="Assign Request", fg_color="#4e9af1", command=submit).pack(fill="x", pady=4)

    def _update_status(self, req_id, status):
        ok, msg = self.maint_ctrl.update_status(req_id, status)
        self.show_message(self.content_area, msg, "#68d391" if ok else "#fc8181")
        self.navigate_to("My Tasks")

    def _resolve_dialog(self, req_id):
        dlg = ctk.CTkToplevel(self.content_area)
        dlg.title("Resolve Maintenance Request")
        dlg.geometry("460x380")
        dlg.grab_set()

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(form, text="Resolve Request", font=("Helvetica",15,"bold"),
                     text_color="white").pack(anchor="w", pady=(0,12))

        ctk.CTkLabel(form, text="Resolution Notes *", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        notes_e = ctk.CTkTextbox(form, height=100)
        notes_e.pack(fill="x", pady=(2,10))

        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x")
        ctk.CTkLabel(row2, text="Time Taken (hrs) *", font=("Helvetica",12), text_color="#94a3b8").grid(row=0,column=0,sticky="w",padx=(0,8),pady=4)
        time_e = ctk.CTkEntry(row2, width=120, placeholder_text="e.g. 2.5")
        time_e.grid(row=0,column=1,padx=(0,16),pady=4)
        ctk.CTkLabel(row2, text="Cost (£) *", font=("Helvetica",12), text_color="#94a3b8").grid(row=0,column=2,sticky="w",padx=(0,8),pady=4)
        cost_e = ctk.CTkEntry(row2, width=120, placeholder_text="e.g. 150")
        cost_e.grid(row=0,column=3,pady=4)

        msg = ctk.CTkLabel(form, text="", font=("Helvetica",11), text_color="#fc8181")
        msg.pack(pady=4)

        def submit():
            notes = notes_e.get("0.0","end").strip()
            if not notes:
                msg.configure(text="Resolution notes required."); return
            try:
                t = float(time_e.get())
                c = float(cost_e.get())
            except ValueError:
                msg.configure(text="Time and cost must be numbers."); return
            ok, m = self.maint_ctrl.resolve_request(req_id, notes, t, c)
            msg.configure(text=m, text_color="#68d391" if ok else "#fc8181")
            if ok:
                dlg.after(1000, dlg.destroy)
                self.navigate_to("My Tasks")

        ctk.CTkButton(form, text="Mark as Resolved", fg_color="#68d391", hover_color="#48bb78",
                      text_color="black", command=submit).pack(fill="x", pady=4)

    def _show_resolve(self):
        """Quick resolve page - all in-progress tasks."""
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Resolve Tasks", "Mark maintenance tasks as completed")

        tasks = self.maint_ctrl.get_all_requests(location=self.location, status="in_progress")
        if not tasks:
            tasks = self.maint_ctrl.get_all_requests(location=self.location, status="scheduled")

        if not tasks:
            ctk.CTkLabel(f, text="No tasks in progress.",
                         text_color="#94a3b8", font=("Helvetica",14)).pack(pady=40)
            return

        for r in tasks:
            card = ctk.CTkFrame(f, fg_color="#1c2333", corner_radius=10)
            card.pack(fill="x", pady=6)
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=12)
            ctk.CTkLabel(row, text=r["issue_title"], font=("Helvetica",13,"bold"),
                         text_color="white").pack(side="left")
            ctk.CTkButton(row, text="Resolve", width=100, height=30,
                          fg_color="#68d391", text_color="black",
                          command=lambda rid=str(r["_id"]): self._resolve_dialog(rid)
                          ).pack(side="right")
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(fill="x", padx=14, pady=(0,10))
            for label, val in [("Tenant",r["tenant_name"]),("Apt",r["apartment_number"]),
                               ("Priority",r.get("priority",""))]:
                ctk.CTkLabel(info, text=f"{label}: {val}", font=("Helvetica",11),
                             text_color="#94a3b8").pack(side="left", padx=(0,16))
