import customtkinter as ctk
from views.base_dashboard import BaseDashboard
from controllers.payment_controller import PaymentController
from controllers.maintenance_controller import MaintenanceController
from controllers.complaint_controller import ComplaintController
from controllers.apartment_controller import ApartmentController
from models.maintenance_model import PRIORITY_LEVELS
from models.complaint_model import COMPLAINT_TYPES
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TenantDashboard(BaseDashboard):
    def __init__(self, master, user):
        nav = [
            ("My Dashboard",  "🏠", self._show_dashboard),
            ("Payments",      "💳", self._show_payments),
            ("Make Payment",  "💰", self._show_make_payment),
            ("Maintenance",   "🔧", self._show_maintenance),
            ("Complaints",    "📝", self._show_complaints),
            ("Payment Charts","📊", self._show_charts),
            ("Settings",      "⚙️", self._show_settings),
        ]
        super().__init__(master, user, nav)
        self.pay_ctrl   = PaymentController()
        self.maint_ctrl = MaintenanceController()
        self.comp_ctrl  = ComplaintController()
        self.apt_ctrl   = ApartmentController()

        # Get tenant & apartment info from user record
        self.tenant_id   = user.get("tenant_id")
        self.apartment_id = user.get("apartment_id")
        self.lease_id    = user.get("lease_id")
        self.navigate_to("My Dashboard")

    # ── DASHBOARD ──────────────────────────────────────────────────────────────
    def _show_dashboard(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, f"Welcome, {self.user.get('full_name','Tenant')} 👋",
                         "Your apartment management portal")

        # Get lease and apartment info
        lease = self.apt_ctrl.get_tenant_lease(self.tenant_id) if self.tenant_id else None
        apt   = self.apt_ctrl.get_apartment_by_id(self.apartment_id) if self.apartment_id else None

        # Info cards row
        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", pady=(0,16))

        apt_num  = apt["apartment_number"] if apt else "N/A"
        location = apt["location"] if apt else self.user.get("location","")
        rent     = f"£{apt['monthly_rent']}/mo" if apt else "N/A"
        lease_end = ""
        if lease and isinstance(lease.get("end_date"), datetime):
            lease_end = lease["end_date"].strftime("%d/%m/%Y")
        lease_status = lease.get("status","").upper() if lease else "N/A"

        for title, val, sub, col in [
            ("Apartment",   apt_num,       location,    "#4e9af1"),
            ("Monthly Rent",rent,          "",          "#68d391"),
            ("Lease Status",lease_status,  "",          "#9f7aea"),
            ("Lease Ends",  lease_end,     "",          "#f6ad55"),
        ]:
            c = self.stat_card(row, title, val, sub, col)
            c.pack(side="left", fill="both", expand=True, padx=4)

        # Alerts
        overdue = [p for p in self.pay_ctrl.get_payments_by_tenant(self.tenant_id)
                   if p.get("status") in ["overdue","pending"]
                   and isinstance(p.get("due_date"),datetime) and p["due_date"] < datetime.utcnow()]
        if overdue:
            alert_card = ctk.CTkFrame(f, fg_color="#2d1515", corner_radius=10)
            alert_card.pack(fill="x", pady=(0,12))
            ctk.CTkLabel(alert_card, text="⚠  Payment Alert",
                         font=("Helvetica",14,"bold"), text_color="#fc8181"
                         ).pack(anchor="w", padx=14, pady=(12,4))
            for p in overdue:
                ctk.CTkLabel(alert_card,
                             text=f"  • Rent of £{p['amount']:.2f} was due on {p['due_date'].strftime('%d/%m/%Y')} — OVERDUE",
                             font=("Helvetica",12), text_color="#fc8181"
                             ).pack(anchor="w", padx=14, pady=1)
            ctk.CTkButton(alert_card, text="Pay Now →", fg_color="#fc8181", hover_color="#c53030",
                          text_color="black", height=34,
                          command=lambda: self.navigate_to("Make Payment")
                          ).pack(anchor="w", padx=14, pady=12)

        # Recent maintenance
        card = self.make_card(f, "Recent Maintenance Requests")
        card.pack(fill="x", pady=(0,12))
        reqs = self.maint_ctrl.get_all_requests(tenant_id=self.tenant_id)[:3]
        if reqs:
            for r in reqs:
                rc = ctk.CTkFrame(card, fg_color="#0d1117", corner_radius=6)
                rc.pack(fill="x", padx=12, pady=3)
                row2 = ctk.CTkFrame(rc, fg_color="transparent")
                row2.pack(fill="x", padx=10, pady=8)
                ctk.CTkLabel(row2, text=r["issue_title"], font=("Helvetica",12),
                             text_color="white").pack(side="left")
                status_col = {"resolved":"#68d391","submitted":"#4e9af1","in_progress":"#9f7aea",
                              "scheduled":"#f6ad55"}.get(r.get("status",""),"white")
                ctk.CTkLabel(row2, text=r.get("status","").upper(),
                             font=("Helvetica",10), text_color=status_col).pack(side="right")
        else:
            ctk.CTkLabel(card, text="No maintenance requests yet.",
                         text_color="#94a3b8", font=("Helvetica",12)).pack(padx=16, pady=12)

    # ── PAYMENTS ──────────────────────────────────────────────────────────────
    def _show_payments(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "My Payment History")

        if not self.tenant_id:
            ctk.CTkLabel(f, text="No tenant record linked to your account.",
                         text_color="#94a3b8").pack(pady=20)
            return

        payments = self.pay_ctrl.get_payments_by_tenant(self.tenant_id)
        status_icons = {"paid":"✅","pending":"⏳","overdue":"🔴","partial":"🟡"}
        rows = [(p.get("invoice_number",""),
                 p["payment_type"],
                 f"£{p['amount']:.2f}",
                 f"£{p.get('amount_paid',0):.2f}",
                 status_icons.get(p["status"],"")+p["status"],
                 p["due_date"].strftime("%d/%m/%Y") if isinstance(p.get("due_date"),datetime) else "",
                 p["paid_date"].strftime("%d/%m/%Y") if isinstance(p.get("paid_date"),datetime) else "-",
                 f"£{p.get('late_fee',0):.2f}")
                for p in payments]

        total_paid = sum(p.get("amount_paid",0) for p in payments if p["status"]=="paid")
        total_pending = sum(p["amount"] for p in payments if p["status"] in ["pending","overdue"])

        sum_row = ctk.CTkFrame(f, fg_color="transparent")
        sum_row.pack(fill="x", pady=(0,12))
        for t, v, c in [("Total Paid",f"£{total_paid:,.2f}","#68d391"),
                        ("Pending/Overdue",f"£{total_pending:,.2f}","#fc8181")]:
            card = self.stat_card(sum_row, t, v, "", c)
            card.pack(side="left", padx=4, fill="both", expand=True)

        tbl = self.make_table(f, ["Invoice","Type","Amount","Paid","Status","Due","Paid On","Late Fee"],
                              rows, [120,100,80,80,120,90,90,80])
        tbl.pack(fill="both", expand=True)

    # ── MAKE PAYMENT ──────────────────────────────────────────────────────────
    def _show_make_payment(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Make a Payment", "Emulated card payment — no real charges")

        if not self.tenant_id:
            ctk.CTkLabel(f, text="No tenant record.", text_color="#94a3b8").pack(pady=20)
            return

        # Outstanding payments
        pending_pays = [p for p in self.pay_ctrl.get_payments_by_tenant(self.tenant_id)
                        if p["status"] in ["pending","overdue","partial"]]

        if not pending_pays:
            ctk.CTkLabel(f, text="✅ No outstanding payments!", text_color="#68d391",
                         font=("Helvetica",16)).pack(pady=40)
            return

        card_outer = self.make_card(f, "Select Payment")
        card_outer.pack(fill="x", pady=(0,16))

        pay_opts = [f"Invoice {p.get('invoice_number','')} — £{p['amount']:.2f} ({p['status']})" for p in pending_pays]
        pay_map  = {f"Invoice {p.get('invoice_number','')} — £{p['amount']:.2f} ({p['status']})": p for p in pending_pays}
        p_var = ctk.StringVar(value=pay_opts[0])
        ctk.CTkOptionMenu(card_outer, values=pay_opts, variable=p_var,
                          fg_color="#1c2333", button_color="#4e9af1",
                          width=450).pack(padx=16, pady=(4,12))

        # Card details
        card_form = self.make_card(f, "💳 Card Details")
        card_form.pack(fill="x", pady=(0,16))
        form = ctk.CTkFrame(card_form, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=(4,12))

        ctk.CTkLabel(form, text="Cardholder Name", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        name_e = ctk.CTkEntry(form, placeholder_text="Name on card")
        name_e.insert(0, self.user.get("full_name",""))
        name_e.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Card Number", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        card_num_e = ctk.CTkEntry(form, placeholder_text="1234 5678 9012 3456")
        card_num_e.pack(fill="x", pady=(2,10))

        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x")
        ctk.CTkLabel(row2, text="Expiry (MM/YY)", font=("Helvetica",12), text_color="#94a3b8").grid(row=0,column=0,sticky="w",padx=(0,8))
        exp_e = ctk.CTkEntry(row2, width=120, placeholder_text="MM/YY")
        exp_e.grid(row=0,column=1,padx=(0,20))
        ctk.CTkLabel(row2, text="CVV", font=("Helvetica",12), text_color="#94a3b8").grid(row=0,column=2,sticky="w",padx=(0,8))
        cvv_e = ctk.CTkEntry(row2, width=80, placeholder_text="CVV", show="•")
        cvv_e.grid(row=0,column=3)

        msg = ctk.CTkLabel(f, text="", font=("Helvetica",12), text_color="#fc8181")
        msg.pack(pady=4)

        def pay():
            sel = p_var.get()
            if sel not in pay_map:
                msg.configure(text="Select valid payment."); return
            p_obj = pay_map[sel]
            ok, result = self.pay_ctrl.validate_card(
                card_num_e.get(), exp_e.get(), cvv_e.get(), name_e.get()
            )
            if not ok:
                msg.configure(text=result, text_color="#fc8181"); return
            card_last4 = result
            ok2, m = self.pay_ctrl.record_payment(str(p_obj["_id"]), p_obj["amount"], card_last4,
                                                  "Tenant online payment")
            if ok2:
                msg.configure(text=f"✅ Payment of £{p_obj['amount']:.2f} processed! Card ending {card_last4}", text_color="#68d391")
                card_num_e.delete(0,"end"); exp_e.delete(0,"end"); cvv_e.delete(0,"end")
            else:
                msg.configure(text=m, text_color="#fc8181")

        ctk.CTkButton(f, text="💳  Pay Now", fg_color="#4e9af1", hover_color="#2b6cb0",
                      height=46, font=("Helvetica",14,"bold"), command=pay).pack(fill="x", pady=4)
        ctk.CTkLabel(f, text="🔒 This is a simulated payment — no real charges will be made.",
                     font=("Helvetica",11), text_color="#718096").pack(pady=4)

    # ── MAINTENANCE ───────────────────────────────────────────────────────────
    def _show_maintenance(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Maintenance Requests", "Submit and track repair requests")

        # Submit new
        card = self.make_card(f, "Submit New Repair Request")
        card.pack(fill="x", pady=(0,16))
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(form, text="Issue Title *", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        title_e = ctk.CTkEntry(form, placeholder_text="Brief description of the issue")
        title_e.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Description *", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        desc_e = ctk.CTkTextbox(form, height=80)
        desc_e.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Priority", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        pri_var = ctk.StringVar(value="Medium")
        ctk.CTkOptionMenu(form, values=PRIORITY_LEVELS, variable=pri_var,
                          fg_color="#1c2333", button_color="#4e9af1").pack(fill="x", pady=(2,10))

        msg_lbl = ctk.CTkLabel(form, text="", font=("Helvetica",11), text_color="#fc8181")
        msg_lbl.pack()

        def submit():
            if not self.apartment_id:
                msg_lbl.configure(text="No apartment assigned."); return
            apt = self.apt_ctrl.get_apartment_by_id(self.apartment_id)
            if not apt:
                msg_lbl.configure(text="Apartment not found."); return
            ttl = title_e.get().strip()
            desc = desc_e.get("0.0","end").strip()
            if not ttl or not desc:
                msg_lbl.configure(text="Title and description required.", text_color="#fc8181"); return
            _, err = self.maint_ctrl.submit_request(
                self.tenant_id, self.user.get("full_name",""),
                self.apartment_id, apt["apartment_number"],
                apt["location"], ttl, desc, pri_var.get(),
                self.user.get("full_name","")
            )
            if err:
                msg_lbl.configure(text=err, text_color="#fc8181")
            else:
                msg_lbl.configure(text="✅ Repair request submitted!", text_color="#68d391")
                title_e.delete(0,"end"); desc_e.delete("0.0","end")
                self._show_maintenance_list(f)

        ctk.CTkButton(form, text="Submit Request", fg_color="#4e9af1", command=submit).pack(fill="x", pady=4)

        self._show_maintenance_list(f)

    def _show_maintenance_list(self, parent):
        for w in parent.winfo_children():
            if hasattr(w, "_maint_list"):
                w.destroy()
        card = self.make_card(parent, "My Repair Requests & Progress")
        card._maint_list = True
        card.pack(fill="x")

        reqs = self.maint_ctrl.get_all_requests(tenant_id=self.tenant_id)
        if not reqs:
            ctk.CTkLabel(card, text="No requests submitted.",
                         text_color="#94a3b8", font=("Helvetica",12)).pack(padx=16, pady=12)
            return

        status_order = {"submitted":0,"investigating":1,"scheduled":2,"in_progress":3,"resolved":4}
        status_color = {"submitted":"#4e9af1","investigating":"#f6ad55","scheduled":"#9f7aea",
                        "in_progress":"#f6ad55","resolved":"#68d391","cancelled":"#fc8181"}

        for r in reqs:
            rc = ctk.CTkFrame(card, fg_color="#0d1117", corner_radius=8)
            rc.pack(fill="x", padx=12, pady=4)
            top = ctk.CTkFrame(rc, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(10,4))
            ctk.CTkLabel(top, text=r["issue_title"], font=("Helvetica",13,"bold"),
                         text_color="white").pack(side="left")
            s = r.get("status","")
            ctk.CTkLabel(top, text=s.upper(), font=("Helvetica",10),
                         text_color=status_color.get(s,"white")).pack(side="right")
            info = ctk.CTkFrame(rc, fg_color="transparent")
            info.pack(fill="x", padx=12, pady=(0,4))
            for label, val in [("Priority",r.get("priority","")),
                               ("Submitted",r["created_at"].strftime("%d/%m/%Y") if isinstance(r.get("created_at"),datetime) else ""),
                               ("Assigned To",r.get("assigned_to","Pending assignment"))]:
                ctk.CTkLabel(info, text=f"{label}: {val}", font=("Helvetica",11),
                             text_color="#94a3b8").pack(side="left", padx=(0,16))
            if r.get("scheduled_date"):
                sched = r["scheduled_date"]
                sched_str = sched.strftime("%d/%m/%Y") if isinstance(sched,datetime) else str(sched)
                ctk.CTkLabel(rc, text=f"📅 Scheduled: {sched_str} at {r.get('scheduled_time','')}",
                             font=("Helvetica",11), text_color="#9f7aea"
                             ).pack(anchor="w", padx=12)
            if r.get("resolution_notes"):
                ctk.CTkLabel(rc, text=f"✅ Resolution: {r['resolution_notes']}",
                             font=("Helvetica",11), text_color="#68d391", wraplength=600, anchor="w"
                             ).pack(fill="x", padx=12)
            if r.get("cost"):
                ctk.CTkLabel(rc, text=f"Cost: £{r['cost']:.2f}  |  Time: {r.get('time_taken_hours',0)}hrs",
                             font=("Helvetica",11), text_color="#94a3b8"
                             ).pack(anchor="w", padx=12, pady=(0,8))
            else:
                ctk.CTkFrame(rc, height=8, fg_color="transparent").pack()

    # ── COMPLAINTS ────────────────────────────────────────────────────────────
    def _show_complaints(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Complaints")

        # Submit
        card = self.make_card(f, "Submit a Complaint")
        card.pack(fill="x", pady=(0,16))
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(form, text="Type", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        ct_var = ctk.StringVar(value=COMPLAINT_TYPES[0])
        ctk.CTkOptionMenu(form, values=COMPLAINT_TYPES, variable=ct_var,
                          fg_color="#1c2333", button_color="#4e9af1").pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Subject *", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        subj_e = ctk.CTkEntry(form, placeholder_text="Brief subject")
        subj_e.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Description *", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        desc_e = ctk.CTkTextbox(form, height=80)
        desc_e.pack(fill="x", pady=(2,10))

        msg_lbl = ctk.CTkLabel(form, text="", font=("Helvetica",11), text_color="#fc8181")
        msg_lbl.pack()

        def submit():
            if not self.apartment_id:
                msg_lbl.configure(text="No apartment assigned."); return
            apt = self.apt_ctrl.get_apartment_by_id(self.apartment_id)
            if not apt:
                msg_lbl.configure(text="Apartment not found."); return
            subj = subj_e.get().strip()
            desc = desc_e.get("0.0","end").strip()
            if not subj or not desc:
                msg_lbl.configure(text="Subject and description required.", text_color="#fc8181"); return
            _, err = self.comp_ctrl.submit_complaint(
                self.tenant_id, self.user.get("full_name",""),
                self.apartment_id, apt["apartment_number"], apt["location"],
                ct_var.get(), subj, desc, self.user.get("full_name","")
            )
            if err:
                msg_lbl.configure(text=err, text_color="#fc8181")
            else:
                msg_lbl.configure(text="✅ Complaint submitted!", text_color="#68d391")
                subj_e.delete(0,"end"); desc_e.delete("0.0","end")

        ctk.CTkButton(form, text="Submit Complaint", fg_color="#4e9af1", command=submit).pack(fill="x",pady=4)

        # List
        card2 = self.make_card(f, "My Complaints")
        card2.pack(fill="x")
        comps = self.comp_ctrl.get_all_complaints(tenant_id=self.tenant_id)
        if comps:
            rows = [(c["complaint_type"], c["subject"][:50], c["status"],
                     c["created_at"].strftime("%d/%m/%Y") if isinstance(c.get("created_at"),datetime) else "",
                     c.get("resolution_notes","") or "Pending")
                    for c in comps]
            self.make_table(card2, ["Type","Subject","Status","Date","Resolution"],
                            rows, [100,220,100,90,180]).pack(fill="x", padx=12, pady=(0,12))
        else:
            ctk.CTkLabel(card2, text="No complaints submitted.", text_color="#94a3b8",
                         font=("Helvetica",12)).pack(padx=16, pady=12)

    # ── CHARTS ────────────────────────────────────────────────────────────────
    def _show_charts(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Payment Charts & Analytics")

        if not self.tenant_id:
            ctk.CTkLabel(f, text="No tenant record.", text_color="#94a3b8").pack(pady=20)
            return

        payments = self.pay_ctrl.get_payments_by_tenant(self.tenant_id)
        paid_payments = [p for p in payments if p["status"] == "paid" and isinstance(p.get("paid_date"),datetime)]

        # ── Chart 1: Payment history line chart ────────────────────────────
        card1 = self.make_card(f, "💳 Payment History")
        card1.pack(fill="x", pady=(0,16))
        if paid_payments:
            paid_payments_sorted = sorted(paid_payments, key=lambda p: p["paid_date"])
            dates  = [p["paid_date"] for p in paid_payments_sorted]
            amounts= [p["amount_paid"] for p in paid_payments_sorted]
            fig, ax = plt.subplots(figsize=(9,3.5))
            fig.patch.set_facecolor("#1c2333")
            ax.set_facecolor("#1c2333")
            ax.plot(dates, amounts, color="#4e9af1", linewidth=2, marker="o", markersize=6, markerfacecolor="white")
            ax.fill_between(dates, amounts, alpha=0.15, color="#4e9af1")
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.xticks(rotation=30, color="#94a3b8")
            ax.tick_params(colors="#94a3b8")
            ax.set_ylabel("£ Amount Paid", color="#94a3b8")
            ax.set_title("Your Payment History", color="white", pad=10)
            for spine in ax.spines.values():
                spine.set_edgecolor("#2d3748")
            plt.tight_layout()
            canvas = FigureCanvasTkAgg(fig, card1)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=8, pady=(0,12))
            plt.close(fig)
        else:
            ctk.CTkLabel(card1, text="No payment history yet.",
                         text_color="#94a3b8", font=("Helvetica",12)).pack(padx=16, pady=20)

        # ── Chart 2: Late payment bar chart ────────────────────────────────
        card2 = self.make_card(f, "⚠  Late Payments History")
        card2.pack(fill="x", pady=(0,16))
        late_payments = [p for p in payments if p.get("late_fee",0) > 0]
        if late_payments:
            late_dates  = [p.get("paid_date") or p.get("due_date") for p in late_payments]
            late_fees   = [p.get("late_fee",0) for p in late_payments]
            late_labels = [d.strftime("%b %Y") if isinstance(d,datetime) else str(d) for d in late_dates]
            fig2, ax2 = plt.subplots(figsize=(7,3))
            fig2.patch.set_facecolor("#1c2333")
            ax2.set_facecolor("#1c2333")
            bars = ax2.bar(late_labels, late_fees, color="#fc8181", width=0.4, edgecolor="none")
            ax2.tick_params(colors="#94a3b8")
            ax2.set_ylabel("Late Fee (£)", color="#94a3b8")
            ax2.set_title("Late Fees by Month", color="white", pad=10)
            for bar, fee in zip(bars, late_fees):
                ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5, f"£{fee:.2f}",
                         ha="center", color="white", fontsize=9)
            for spine in ax2.spines.values():
                spine.set_edgecolor("#2d3748")
            plt.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, card2)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="x", padx=8, pady=(0,12))
            plt.close(fig2)
        else:
            ctk.CTkLabel(card2, text="✅ No late payments on record!",
                         text_color="#68d391", font=("Helvetica",12)).pack(padx=16, pady=20)

        # ── Chart 3: Neighbour comparison ──────────────────────────────────
        card3 = self.make_card(f, "🏘  Payment Comparison with Neighbours")
        card3.pack(fill="x", pady=(0,16))
        if self.apartment_id:
            neighbor_data = self.pay_ctrl.get_neighbor_payments(self.tenant_id, self.apartment_id)
            if neighbor_data:
                labels = [n["apartment_number"] for n in neighbor_data]
                paid_v = [n["paid"] for n in neighbor_data]
                pend_v = [n["pending"] for n in neighbor_data]
                x = range(len(labels))
                width = 0.35
                fig3, ax3 = plt.subplots(figsize=(9,3.5))
                fig3.patch.set_facecolor("#1c2333")
                ax3.set_facecolor("#1c2333")
                bars1 = ax3.bar([i-width/2 for i in x], paid_v, width, label="Paid", color="#68d391", edgecolor="none")
                bars2 = ax3.bar([i+width/2 for i in x], pend_v, width, label="Pending", color="#f6ad55", edgecolor="none")
                ax3.set_xticks(list(x))
                ax3.set_xticklabels(labels, rotation=20, ha="right", color="#94a3b8")
                ax3.tick_params(colors="#94a3b8")
                ax3.set_ylabel("£", color="#94a3b8")
                ax3.set_title("Payment Comparison with Neighbours (Last 6 months)", color="white", pad=10)
                ax3.legend(facecolor="#1c2333", labelcolor="white")
                for spine in ax3.spines.values():
                    spine.set_edgecolor("#2d3748")
                plt.tight_layout()
                canvas3 = FigureCanvasTkAgg(fig3, card3)
                canvas3.draw()
                canvas3.get_tk_widget().pack(fill="x", padx=8, pady=(0,12))
                plt.close(fig3)
            else:
                ctk.CTkLabel(card3, text="Neighbour data not available.",
                             text_color="#94a3b8", font=("Helvetica",12)).pack(padx=16, pady=20)
        else:
            ctk.CTkLabel(card3, text="No apartment assigned.",
                         text_color="#94a3b8", font=("Helvetica",12)).pack(padx=16, pady=20)

    # ── SETTINGS ───────────────────────────────────────────────────────────────
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
            ("Phone", self.user.get("phone", "N/A")),
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

            from controllers.user_controller import UserController
            user_ctrl = UserController()
            success, error = user_ctrl.change_password(self.user["_id"], current, new)
            
            if success:
                msg.configure(text="✅ Password changed successfully!", text_color="#68d391")
                current_pw.delete(0, "end")
                new_pw.delete(0, "end")
                confirm_pw.delete(0, "end")
            else:
                msg.configure(text=error, text_color="#fc8181")

        ctk.CTkButton(form, text="Change Password", fg_color="#4e9af1", hover_color="#2b6cb0",
                     command=change_password).pack(fill="x", pady=8)
