import customtkinter as ctk
from views.base_dashboard import BaseDashboard
from controllers.user_controller import UserController
from controllers.apartment_controller import ApartmentController
from controllers.tenant_controller import TenantController
from controllers.report_controller import ReportController
from controllers.auth_controller import AuthController
from models.apartment_model import APARTMENT_TYPES
from datetime import datetime

class AdminDashboard(BaseDashboard):
    def __init__(self, master, user):
        nav = [
            ("Dashboard",  "📊", self._show_dashboard),
            ("Users",      "👥", self._show_users),
            ("Apartments", "🏢", self._show_apartments),
            ("Leases",     "📋", self._show_leases),
            ("Reports",    "📈", self._show_reports),
            ("Settings",   "⚙️", self._show_settings),
        ]
        super().__init__(master, user, nav)
        self.user_ctrl = UserController()
        self.apt_ctrl  = ApartmentController()
        self.ten_ctrl  = TenantController()
        self.rpt_ctrl  = ReportController()
        self.auth      = AuthController()
        self.location  = user.get("location")
        self.navigate_to("Dashboard")

    # ── DASHBOARD ──────────────────────────────────────────────────────────────
    def _show_dashboard(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, f"Admin Dashboard — {self.location}", "Location overview")

        occ = self.apt_ctrl.get_occupancy_stats(self.location)
        fin = self.rpt_ctrl.financial_report(self.location)

        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", pady=(0,16))
        for title, val, sub, col in [
            ("Total Apartments", occ["total"], "", "#4e9af1"),
            ("Occupied", occ["occupied"], f"{round(occ['occupied']/occ['total']*100,1) if occ['total'] else 0}%", "#68d391"),
            ("Available", occ["available"], "Ready to lease", "#f6ad55"),
            ("Revenue Collected", f"£{fin['collected']:,.0f}", f"Pending: £{fin['pending']:,.0f}", "#9f7aea"),
        ]:
            c = self.stat_card(row, title, val, sub, col)
            c.pack(side="left", fill="both", expand=True, padx=4)

        # Upcoming lease expirations
        card = self.make_card(f, "⚠  Leases Expiring Soon")
        card.pack(fill="x", pady=(0,12))
        leases = self.apt_ctrl.get_all_leases(location=self.location, status="active")
        soon = []
        for l in leases:
            end = l.get("end_date")
            if end and isinstance(end, datetime):
                days = (end - datetime.utcnow()).days
                if 0 <= days <= 60:
                    soon.append((l["tenant_name"], l["apartment_number"], end.strftime("%d/%m/%Y"), days))
        if soon:
            tbl = self.make_table(card, ["Tenant","Apt #","Expires","Days Left"],
                                  soon, [180,100,110,80])
            tbl.pack(fill="x", padx=12, pady=(0,12))
        else:
            ctk.CTkLabel(card, text="No leases expiring in the next 60 days.",
                         text_color="#94a3b8", font=("Helvetica",12)).pack(padx=16, pady=12)

    # ── USERS ──────────────────────────────────────────────────────────────────
    def _show_users(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "User Management", f"Staff accounts for {self.location}")

        # Add user button
        top_row = ctk.CTkFrame(f, fg_color="transparent")
        top_row.pack(fill="x", pady=(0,12))
        ctk.CTkButton(top_row, text="+ Add User", fg_color="#4e9af1", hover_color="#2b6cb0",
                      command=lambda: self._add_user_dialog(f)).pack(side="right")

        users = self.user_ctrl.get_all_users(location=self.location)
        non_tenant = [u for u in users if u.get("role") != "tenant"]
        role_labels = {"admin":"Admin","manager":"Manager","front_desk":"Front Desk",
                       "finance_manager":"Finance","maintenance_staff":"Maintenance"}
        rows = [(u["full_name"], u["username"], role_labels.get(u["role"],u["role"]),
                 u.get("email",""), "✅ Active" if u.get("is_active") else "❌ Inactive")
                for u in non_tenant]
        tbl = self.make_table(f, ["Name","Username","Role","Email","Status"],
                              rows, [160,120,120,200,90])
        tbl.pack(fill="both", expand=True)

    def _add_user_dialog(self, parent):
        dlg = ctk.CTkToplevel(parent)
        dlg.title("Add New User")
        dlg.geometry("480x540")
        dlg.grab_set()
        dlg.resizable(False, False)

        ctk.CTkLabel(dlg, text="Add Staff User", font=("Helvetica",16,"bold")).pack(pady=(16,4))
        ctk.CTkFrame(dlg, height=1, fg_color="#2d3748").pack(fill="x", padx=16, pady=4)

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=8)

        fields = {}
        for label, ph in [("Full Name","Full name"),("Username","Username"),
                           ("Email","Email address"),("Phone","Phone number"),
                           ("Password","Password (min 8 chars)")]:
            ctk.CTkLabel(form, text=label, font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
            e = ctk.CTkEntry(form, placeholder_text=ph, show="•" if "Pass" in label else "")
            e.pack(fill="x", pady=(2,10))
            fields[label] = e

        ctk.CTkLabel(form, text="Role", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        role_var = ctk.StringVar(value="front_desk")
        ctk.CTkOptionMenu(form, values=["front_desk","finance_manager","maintenance_staff","admin"],
                          variable=role_var, fg_color="#1c2333", button_color="#4e9af1").pack(fill="x",pady=(2,10))

        msg = ctk.CTkLabel(form, text="", font=("Helvetica",11), text_color="#fc8181")
        msg.pack()

        def submit():
            from utils.validators import validate_email, validate_phone, validate_password
            fn = fields["Full Name"].get().strip()
            un = fields["Username"].get().strip()
            em = fields["Email"].get().strip()
            ph = fields["Phone"].get().strip()
            pw = fields["Password"].get()
            if not all([fn,un,em,ph,pw]):
                msg.configure(text="All fields required.")
                return
            if not validate_email(em):
                msg.configure(text="Invalid email.")
                return
            ok, err = validate_password(pw)
            if not ok:
                msg.configure(text=err)
                return
            _, err = self.user_ctrl.create_user(un, pw, role_var.get(), fn, em, ph,
                                                self.location, self.user["username"])
            if err:
                msg.configure(text=err, text_color="#fc8181")
            else:
                msg.configure(text="User created!", text_color="#68d391")
                dlg.after(1000, dlg.destroy)

        ctk.CTkButton(form, text="Create User", fg_color="#4e9af1", hover_color="#2b6cb0",
                      command=submit).pack(fill="x", pady=8)

    # ── APARTMENTS ─────────────────────────────────────────────────────────────
    def _show_apartments(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Apartment Management", f"All apartments in {self.location}")

        top_row = ctk.CTkFrame(f, fg_color="transparent")
        top_row.pack(fill="x", pady=(0,12))

        # Status filter
        status_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(top_row, values=["All","available","occupied","maintenance"],
                          variable=status_var, fg_color="#1c2333", button_color="#4e9af1",
                          command=lambda v: self._refresh_apts(f, v)).pack(side="left", padx=(0,8))
        ctk.CTkButton(top_row, text="+ Register Apartment", fg_color="#4e9af1", hover_color="#2b6cb0",
                      command=lambda: self._add_apt_dialog(f)).pack(side="right")

        self._refresh_apts(f, "All")

    def _refresh_apts(self, parent, status_filter):
        # Destroy existing table container if present
        if hasattr(parent, "_apt_table_container"):
            if parent._apt_table_container is not None and parent._apt_table_container.winfo_exists():
                parent._apt_table_container.destroy()
        
        loc = self.location
        status = None if status_filter == "All" else status_filter
        apts = self.apt_ctrl.get_all_apartments(location=loc, status=status)
        status_colors = {"available":"#68d391","occupied":"#f6ad55","maintenance":"#fc8181","unavailable":"#94a3b8"}
        rows = [(a["apartment_number"], a["apartment_type"], a["num_rooms"],
                 f"£{a['monthly_rent']}", a["floor"], a.get("size_sqft","?"),
                 a["status"]) for a in apts]
        
        # Create container for table with filter header
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True)
        parent._apt_table_container = container
        
        # Show filter status
        if status_filter != "All":
            ctk.CTkLabel(container, text=f"Filter: Status = {status_filter}", font=("Helvetica",11), 
                        text_color="#4e9af1").pack(fill="x", pady=(0,8))
        
        tbl = self.make_table(container, ["Apt #","Type","Rooms","Rent","Floor","Sqft","Status"],
                              rows, [90,110,70,80,60,70,100])
        tbl.pack(fill="both", expand=True)

    def _add_apt_dialog(self, parent):
        dlg = ctk.CTkToplevel(parent)
        dlg.title("Register Apartment")
        dlg.geometry("480x560")
        dlg.grab_set()
        dlg.resizable(False, False)

        ctk.CTkLabel(dlg, text="Register New Apartment", font=("Helvetica",16,"bold")).pack(pady=(16,4))
        ctk.CTkFrame(dlg, height=1, fg_color="#2d3748").pack(fill="x", padx=16, pady=4)

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=8)

        fields = {}
        for label, ph in [("Apt Number","e.g. BR-101"),("Monthly Rent","e.g. 950"),
                          ("Floor","e.g. 2"),("Size (sqft)","e.g. 750")]:
            ctk.CTkLabel(form, text=label, font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
            e = ctk.CTkEntry(form, placeholder_text=ph)
            e.pack(fill="x", pady=(2,10))
            fields[label] = e

        ctk.CTkLabel(form, text="Type", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        type_var = ctk.StringVar(value="2-Bedroom")
        ctk.CTkOptionMenu(form, values=APARTMENT_TYPES, variable=type_var,
                          fg_color="#1c2333", button_color="#4e9af1").pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Num Rooms", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        rooms_var = ctk.StringVar(value="2")
        ctk.CTkOptionMenu(form, values=["0","1","2","3","4","5"], variable=rooms_var,
                          fg_color="#1c2333", button_color="#4e9af1").pack(fill="x", pady=(2,10))

        msg = ctk.CTkLabel(form, text="", font=("Helvetica",11), text_color="#fc8181")
        msg.pack()

        def submit():
            num = fields["Apt Number"].get().strip()
            try:
                rent  = float(fields["Monthly Rent"].get())
                floor = int(fields["Floor"].get())
                sqft  = int(fields["Size (sqft)"].get())
            except ValueError:
                msg.configure(text="Rent/Floor/Size must be numbers."); return
            if not num:
                msg.configure(text="Apartment number required."); return
            _, err = self.apt_ctrl.register_apartment(
                num, self.location, type_var.get(), rent,
                int(rooms_var.get()), floor, sqft, [], self.user["username"]
            )
            if err:
                msg.configure(text=err, text_color="#fc8181")
            else:
                msg.configure(text="Apartment registered!", text_color="#68d391")
                dlg.after(1000, dlg.destroy)

        ctk.CTkButton(form, text="Register Apartment", fg_color="#4e9af1",
                      command=submit).pack(fill="x", pady=8)

    # ── LEASES ─────────────────────────────────────────────────────────────────
    def _show_leases(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Lease Agreements", f"Active leases in {self.location}")

        leases = self.apt_ctrl.get_all_leases(location=self.location)
        rows = []
        for l in leases:
            end = l.get("end_date")
            end_str = end.strftime("%d/%m/%Y") if isinstance(end, datetime) else str(end)
            start_str = l["start_date"].strftime("%d/%m/%Y") if isinstance(l.get("start_date"), datetime) else ""
            days_left = (end - datetime.utcnow()).days if isinstance(end, datetime) else "?"
            rows.append((l["tenant_name"], l["apartment_number"], start_str,
                         end_str, f"£{l['monthly_rent']}", l["status"], days_left))
        tbl = self.make_table(f, ["Tenant","Apt #","Start","End","Rent","Status","Days Left"],
                              rows, [160,90,100,100,80,100,70])
        tbl.pack(fill="both", expand=True)

    # ── REPORTS ────────────────────────────────────────────────────────────────
    def _show_reports(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Location Reports", f"Financial & maintenance reports for {self.location}")

        fin = self.rpt_ctrl.financial_report(self.location)
        maint = self.rpt_ctrl.maintenance_cost_report(self.location)

        card = self.make_card(f, "Financial Summary")
        card.pack(fill="x", pady=(0,12))
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(4,12))
        for label, val, col in [
            ("Total Due", f"£{fin['total_due']:,.2f}", "#e2e8f0"),
            ("Collected", f"£{fin['collected']:,.2f}", "#68d391"),
            ("Pending", f"£{fin['pending']:,.2f}", "#f6ad55"),
            ("Overdue", f"£{fin['overdue']:,.2f}", "#fc8181"),
            ("Late Fees", f"£{fin['late_fees']:,.2f}", "#9f7aea"),
        ]:
            s = ctk.CTkFrame(row, fg_color="#0d1117", corner_radius=8)
            s.pack(side="left", padx=4, fill="both", expand=True)
            ctk.CTkLabel(s, text=val, font=("Helvetica",16,"bold"), text_color=col).pack(pady=(10,2))
            ctk.CTkLabel(s, text=label, font=("Helvetica",11), text_color="#94a3b8").pack(pady=(0,10))

        mc = self.make_card(f, "Maintenance Summary")
        mc.pack(fill="x", pady=(0,12))
        r2 = ctk.CTkFrame(mc, fg_color="transparent")
        r2.pack(fill="x", padx=12, pady=(4,12))
        for label, val, col in [
            ("Resolved", maint["total_resolved"], "#68d391"),
            ("Total Cost", f"£{maint['total_cost']:,.2f}", "#4e9af1"),
            ("Total Hours", f"{maint['total_hours']:.1f}h", "#f6ad55"),
        ]:
            s = ctk.CTkFrame(r2, fg_color="#0d1117", corner_radius=8)
            s.pack(side="left", padx=4, fill="both", expand=True)
            ctk.CTkLabel(s, text=str(val), font=("Helvetica",16,"bold"), text_color=col).pack(pady=(10,2))
            ctk.CTkLabel(s, text=label, font=("Helvetica",11), text_color="#94a3b8").pack(pady=(0,10))

    # ── SETTINGS ───────────────────────────────────────────────────────────────
    def _show_settings(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Admin Settings", "Manage your account and reset user passwords")

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
        card2.pack(fill="x", pady=(0,16))
        
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

        # Reset User Password Card
        card3 = self.make_card(f, "🔑 Reset User Password")
        card3.pack(fill="x")
        
        form2 = ctk.CTkFrame(card3, fg_color="transparent")
        form2.pack(fill="x", padx=16, pady=12)

        users = self.user_ctrl.get_all_users(location=self.location)
        non_self = [u for u in users if str(u.get("_id")) != str(self.user.get("_id"))]
        
        if non_self:
            user_opts = [f"{u['full_name']} ({u['username']})" for u in non_self]
            user_map = {f"{u['full_name']} ({u['username']})": u for u in non_self}
            
            ctk.CTkLabel(form2, text="Select User *", font=("Helvetica",12), 
                        text_color="#94a3b8", anchor="w").pack(fill="x")
            user_var = ctk.StringVar(value=user_opts[0] if user_opts else "")
            ctk.CTkOptionMenu(form2, values=user_opts, variable=user_var,
                            fg_color="#1c2333", button_color="#4e9af1").pack(fill="x", pady=(2,10))

            ctk.CTkLabel(form2, text="New Password *", font=("Helvetica",12), 
                        text_color="#94a3b8", anchor="w").pack(fill="x")
            reset_pw = ctk.CTkEntry(form2, placeholder_text="New password (min 8 chars)", show="•")
            reset_pw.pack(fill="x", pady=(2,10))

            ctk.CTkLabel(form2, text="Confirm Password *", font=("Helvetica",12), 
                        text_color="#94a3b8", anchor="w").pack(fill="x")
            reset_confirm = ctk.CTkEntry(form2, placeholder_text="Confirm password", show="•")
            reset_confirm.pack(fill="x", pady=(2,10))

            msg2 = ctk.CTkLabel(form2, text="", font=("Helvetica",11), text_color="#fc8181")
            msg2.pack()

            def reset_user_password():
                from utils.validators import validate_password
                sel_user = user_var.get()
                new = reset_pw.get()
                confirm = reset_confirm.get()

                if sel_user not in user_map:
                    msg2.configure(text="Please select a valid user.", text_color="#fc8181")
                    return
                if not new or not confirm:
                    msg2.configure(text="All fields required.", text_color="#fc8181")
                    return
                if new != confirm:
                    msg2.configure(text="Passwords do not match.", text_color="#fc8181")
                    return
                
                ok, err = validate_password(new)
                if not ok:
                    msg2.configure(text=err, text_color="#fc8181")
                    return

                user = user_map[sel_user]
                success, error = self.user_ctrl.admin_reset_password(user["_id"], new)
                
                if success:
                    msg2.configure(text=f"✅ {error}", text_color="#68d391")
                    reset_pw.delete(0, "end")
                    reset_confirm.delete(0, "end")
                else:
                    msg2.configure(text=error, text_color="#fc8181")

            ctk.CTkButton(form2, text="Reset Password", fg_color="#f6ad55", hover_color="#d98e1b",
                         command=reset_user_password).pack(fill="x", pady=8)
        else:
            ctk.CTkLabel(form2, text="No other users in your location.", text_color="#94a3b8",
                        font=("Helvetica",12)).pack(padx=16, pady=20)
