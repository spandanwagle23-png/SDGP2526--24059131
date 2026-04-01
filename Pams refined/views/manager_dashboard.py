import customtkinter as ctk
from views.base_dashboard import BaseDashboard
from controllers.apartment_controller import ApartmentController
from controllers.report_controller import ReportController
from controllers.user_controller import UserController
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ManagerDashboard(BaseDashboard):
    def __init__(self, master, user):
        nav = [
            ("Overview",    "📊", self._show_overview),
            ("Occupancy",   "🏢", self._show_occupancy),
            ("Reports",     "📈", self._show_reports),
            ("Manage Admins", "🔑", self._show_manage_admins),
            ("Expand City", "🌍", self._show_expand),
        ]
        super().__init__(master, user, nav)
        self.apt_ctrl = ApartmentController()
        self.rpt_ctrl = ReportController()
        self.user_ctrl = UserController()
        self.navigate_to("Overview")

    def _show_overview(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Manager Overview", "System-wide performance snapshot")

        report = self.rpt_ctrl.occupancy_report()
        fin = self.rpt_ctrl.financial_report()

        # Top stat cards
        total_apts = sum(r["total"] for r in report)
        total_occ  = sum(r["occupied"] for r in report)
        occ_rate   = round(total_occ/total_apts*100, 1) if total_apts else 0

        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", pady=(0,16))
        cards = [
            ("Total Apartments", total_apts, "", "#4e9af1"),
            ("Occupied", total_occ, f"{occ_rate}% occupancy", "#68d391"),
            ("Available", total_apts - total_occ, "Ready to lease", "#f6ad55"),
            ("Revenue Collected", f"£{fin['collected']:,.0f}", "This period", "#9f7aea"),
        ]
        for title, val, sub, col in cards:
            c = self.stat_card(row, title, val, sub, col)
            c.pack(side="left", fill="both", expand=True, padx=4)

        # Occupancy by city chart
        if report:
            card = self.make_card(f, "Occupancy by City")
            card.pack(fill="x", pady=(0,16))
            cities = [r["location"] for r in report]
            rates  = [r["occupancy_rate"] for r in report]
            fig, ax = plt.subplots(figsize=(8,3))
            fig.patch.set_facecolor("#1c2333")
            ax.set_facecolor("#1c2333")
            bars = ax.bar(cities, rates, color="#4e9af1", width=0.5, edgecolor="none")
            ax.set_ylim(0, 110)
            ax.set_ylabel("Occupancy %", color="#94a3b8")
            ax.tick_params(colors="#94a3b8")
            for bar, rate in zip(bars, rates):
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+2, f"{rate}%",
                        ha="center", color="white", fontsize=9)
            for spine in ax.spines.values():
                spine.set_edgecolor("#2d3748")
            plt.tight_layout()
            canvas = FigureCanvasTkAgg(fig, card)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=8, pady=(0,12))
            plt.close(fig)

    def _show_occupancy(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Occupancy Report", "Apartment occupancy across all locations")

        report = self.rpt_ctrl.occupancy_report()
        for r in report:
            card = self.make_card(f, r["location"])
            card.pack(fill="x", pady=(0,10))
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=(4,12))
            items = [
                ("Total", r["total"], "#e2e8f0"),
                ("Occupied", r["occupied"], "#68d391"),
                ("Available", r["available"], "#4e9af1"),
                ("Maintenance", r["maintenance"], "#f6ad55"),
                ("Rate", f"{r['occupancy_rate']}%", "#9f7aea"),
            ]
            for label, val, col in items:
                s = ctk.CTkFrame(row, fg_color="#0d1117", corner_radius=8)
                s.pack(side="left", padx=4, fill="both", expand=True)
                ctk.CTkLabel(s, text=str(val), font=("Helvetica",20,"bold"), text_color=col).pack(pady=(10,2))
                ctk.CTkLabel(s, text=label, font=("Helvetica",11), text_color="#94a3b8").pack(pady=(0,10))

    def _show_reports(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Performance Reports")

        # Location filter
        ctrl_row = ctk.CTkFrame(f, fg_color="transparent")
        ctrl_row.pack(fill="x", pady=(0,12))
        ctk.CTkLabel(ctrl_row, text="Filter by Location:", font=("Helvetica",13),
                     text_color="#94a3b8").pack(side="left", padx=(0,8))
        locations = ["All"] + self.rpt_ctrl.get_all_locations()
        self.loc_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(ctrl_row, values=locations, variable=self.loc_var,
                          fg_color="#1c2333", button_color="#4e9af1",
                          command=lambda v: self._render_financial(f, v)).pack(side="left")
        self._render_financial(f, "All")

    def _render_financial(self, parent, location):
        # Destroy existing report container if present
        if hasattr(parent, "_report_container"):
            if parent._report_container is not None and parent._report_container.winfo_exists():
                parent._report_container.destroy()
        
        loc = None if location == "All" else location
        fin = self.rpt_ctrl.financial_report(loc)
        maint = self.rpt_ctrl.maintenance_cost_report(loc)

        # Create container for reports with filter header
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x")
        parent._report_container = container
        
        # Show filter status
        if location != "All":
            ctk.CTkLabel(container, text=f"Filter: Location = {location}", font=("Helvetica",11), 
                        text_color="#4e9af1").pack(fill="x", pady=(0,8))

        # Financial summary
        card = self.make_card(container, "Financial Summary")
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

        # Maintenance cost
        mc = self.make_card(container, "Maintenance Cost Summary")
        mc.pack(fill="x", pady=(0,12))
        r2 = ctk.CTkFrame(mc, fg_color="transparent")
        r2.pack(fill="x", padx=12, pady=(4,12))
        for label, val, col in [
            ("Resolved Issues", maint["total_resolved"], "#68d391"),
            ("Total Cost", f"£{maint['total_cost']:,.2f}", "#4e9af1"),
            ("Total Hours", f"{maint['total_hours']:.1f}h", "#f6ad55"),
        ]:
            s = ctk.CTkFrame(r2, fg_color="#0d1117", corner_radius=8)
            s.pack(side="left", padx=4, fill="both", expand=True)
            ctk.CTkLabel(s, text=str(val), font=("Helvetica",16,"bold"), text_color=col).pack(pady=(10,2))
            ctk.CTkLabel(s, text=label, font=("Helvetica",11), text_color="#94a3b8").pack(pady=(0,10))

    def _show_manage_admins(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Manage Admins", "Create and manage location admins")

        # Create admin button
        top_row = ctk.CTkFrame(f, fg_color="transparent")
        top_row.pack(fill="x", pady=(0,12))
        ctk.CTkButton(top_row, text="+ Create Admin", fg_color="#4e9af1", hover_color="#2b6cb0",
                      command=lambda: self._create_admin_dialog()).pack(side="right")

        # List all admins
        all_users = self.user_ctrl.get_all_users()
        admins = [u for u in all_users if u.get("role") == "admin"]
        
        if not admins:
            ctk.CTkLabel(f, text="No admins created yet.", text_color="#94a3b8", 
                         font=("Helvetica",12)).pack(pady=40)
            return

        rows = [(a["full_name"], a["username"], a.get("location","System"), 
                 a.get("email",""), "✅ Active" if a.get("is_active") else "❌ Inactive")
                for a in admins]
        tbl = self.make_table(f, ["Full Name","Username","Location","Email","Status"],
                              rows, [180,140,130,200,100])
        tbl.pack(fill="both", expand=True)

    def _create_admin_dialog(self):
        dlg = ctk.CTkToplevel(self.content_area)
        dlg.title("Create New Admin")
        dlg.geometry("500x580")
        dlg.grab_set()
        dlg.resizable(False, False)

        ctk.CTkLabel(dlg, text="Create Location Admin", font=("Helvetica",16,"bold")).pack(pady=(16,4))
        ctk.CTkFrame(dlg, height=1, fg_color="#2d3748").pack(fill="x", padx=16, pady=4)

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=8)

        fields = {}
        for label, ph in [("Full Name","Full name"), ("Username","Username"),
                          ("Email","Email address"), ("Phone","Phone number"),
                          ("Password","Password (min 8 chars)")]:
            ctk.CTkLabel(form, text=label, font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
            e = ctk.CTkEntry(form, placeholder_text=ph, show="•" if "Pass" in label else "")
            e.pack(fill="x", pady=(2,10))
            fields[label] = e

        # Location selection
        ctk.CTkLabel(form, text="City/Location *", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        locations = []
        try:
            locations = [l["city"] for l in self.user_ctrl.get_locations()]
        except:
            locations = ["Bristol", "London", "Cardiff", "Manchester"]
        
        loc_var = ctk.StringVar(value=locations[0] if locations else "")
        ctk.CTkOptionMenu(form, values=locations, variable=loc_var,
                          fg_color="#1c2333", button_color="#4e9af1").pack(fill="x", pady=(2,10))

        msg = ctk.CTkLabel(form, text="", font=("Helvetica",11), text_color="#fc8181")
        msg.pack()

        def submit():
            from utils.validators import validate_email, validate_phone, validate_password
            fn = fields["Full Name"].get().strip()
            un = fields["Username"].get().strip()
            em = fields["Email"].get().strip()
            ph = fields["Phone"].get().strip()
            pw = fields["Password"].get()
            loc = loc_var.get()
            
            if not all([fn, un, em, ph, pw, loc]):
                msg.configure(text="All fields required.")
                return
            if not validate_email(em):
                msg.configure(text="Invalid email.")
                return
            ok, err = validate_password(pw)
            if not ok:
                msg.configure(text=err)
                return
            
            _, err = self.user_ctrl.create_user(un, pw, "admin", fn, em, ph, loc, self.user["username"])
            if err:
                msg.configure(text=err, text_color="#fc8181")
            else:
                msg.configure(text=f"✅ Admin created for {loc}!", text_color="#68d391")
                dlg.after(1500, dlg.destroy)

        ctk.CTkButton(form, text="Create Admin", fg_color="#4e9af1", hover_color="#2b6cb0",
                      command=submit).pack(fill="x", pady=8)

    def _show_expand(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Expand Business", "Add a new city/branch location")

        card = self.make_card(f)
        card.pack(fill="x", pady=(0,16))

        existing = [l["city"] for l in self.user_ctrl.get_locations()]
        ctk.CTkLabel(card, text="Existing Locations:", font=("Helvetica",13,"bold"),
                     text_color="white").pack(anchor="w", padx=16, pady=(14,4))
        ctk.CTkLabel(card, text="  •  " + "\n  •  ".join(existing),
                     font=("Helvetica",12), text_color="#94a3b8").pack(anchor="w", padx=16, pady=(0,12))

        ctk.CTkFrame(card, height=1, fg_color="#2d3748").pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(card, text="Add New Location", font=("Helvetica",13,"bold"),
                     text_color="white").pack(anchor="w", padx=16, pady=(12,8))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=16, pady=(0,16))

        ctk.CTkLabel(form, text="City Name", font=("Helvetica",12), text_color="#94a3b8").grid(row=0,column=0,sticky="w",padx=4,pady=4)
        city_e = ctk.CTkEntry(form, width=220, placeholder_text="e.g. Birmingham")
        city_e.grid(row=0,column=1,padx=8,pady=4)

        ctk.CTkLabel(form, text="Office Address", font=("Helvetica",12), text_color="#94a3b8").grid(row=1,column=0,sticky="w",padx=4,pady=4)
        addr_e = ctk.CTkEntry(form, width=320, placeholder_text="Full address")
        addr_e.grid(row=1,column=1,padx=8,pady=4)

        msg_lbl = ctk.CTkLabel(form, text="", font=("Helvetica",12), text_color="#fc8181")
        msg_lbl.grid(row=2,column=0,columnspan=2,pady=4)

        def add_loc():
            city = city_e.get().strip()
            addr = addr_e.get().strip()
            if not city or not addr:
                msg_lbl.configure(text="All fields required.", text_color="#fc8181")
                return
            _, err = self.user_ctrl.add_location(city, addr, self.user["username"])
            if err:
                msg_lbl.configure(text=err, text_color="#fc8181")
            else:
                msg_lbl.configure(text=f"Location '{city}' added!", text_color="#68d391")
                city_e.delete(0,"end"); addr_e.delete(0,"end")

        ctk.CTkButton(form, text="Add Location", fg_color="#4e9af1", hover_color="#2b6cb0",
                      command=add_loc).grid(row=3,column=0,columnspan=2,pady=8)
