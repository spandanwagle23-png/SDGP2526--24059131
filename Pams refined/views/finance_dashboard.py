import customtkinter as ctk
from views.base_dashboard import BaseDashboard
from controllers.payment_controller import PaymentController
from controllers.tenant_controller import TenantController
from controllers.apartment_controller import ApartmentController
from controllers.report_controller import ReportController
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class FinanceDashboard(BaseDashboard):
    def __init__(self, master, user):
        nav = [
            ("Dashboard",    "📊", self._show_dashboard),
            ("Invoices",     "🧾", self._show_invoices),
            ("Payments",     "💳", self._show_payments),
            ("Overdue",      "⚠️", self._show_overdue),
            ("Create Invoice","➕", self._show_create_invoice),
            ("Reports",      "📈", self._show_reports),
        ]
        super().__init__(master, user, nav)
        self.pay_ctrl = PaymentController()
        self.ten_ctrl = TenantController()
        self.apt_ctrl = ApartmentController()
        self.rpt_ctrl = ReportController()
        self.location = user.get("location")
        self.navigate_to("Dashboard")

    def _show_dashboard(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Finance Overview", f"Location: {self.location}")

        fin = self.rpt_ctrl.financial_report(self.location)
        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", pady=(0,16))
        for t, v, c in [
            ("Total Due", f"£{fin['total_due']:,.2f}", "#e2e8f0"),
            ("Collected", f"£{fin['collected']:,.2f}", "#68d391"),
            ("Pending",   f"£{fin['pending']:,.2f}",   "#f6ad55"),
            ("Overdue",   f"£{fin['overdue']:,.2f}",   "#fc8181"),
            ("Late Fees", f"£{fin['late_fees']:,.2f}", "#9f7aea"),
        ]:
            card = self.stat_card(row, t, v, "", c)
            card.pack(side="left", fill="both", expand=True, padx=4)

        # Bar chart: collected vs pending
        card = self.make_card(f, "Collections Summary")
        card.pack(fill="x", pady=(0,16))
        fig, ax = plt.subplots(figsize=(6,3))
        fig.patch.set_facecolor("#1c2333")
        ax.set_facecolor("#1c2333")
        categories = ["Collected", "Pending", "Overdue"]
        values = [fin["collected"], fin["pending"], fin["overdue"]]
        colors = ["#68d391", "#f6ad55", "#fc8181"]
        bars = ax.bar(categories, values, color=colors, width=0.4, edgecolor="none")
        ax.tick_params(colors="#94a3b8")
        ax.set_ylabel("£", color="#94a3b8")
        for bar, val in zip(bars, values):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+20, f"£{val:,.0f}",
                    ha="center", color="white", fontsize=9)
        for spine in ax.spines.values():
            spine.set_edgecolor("#2d3748")
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=8, pady=(0,12))
        plt.close(fig)

        # Recent payments
        card2 = self.make_card(f, "Recent Payments")
        card2.pack(fill="x")
        payments = self.pay_ctrl.get_all_payments(location=self.location, status="paid")[:8]
        rows = [(p["tenant_name"], p["apartment_number"], f"£{p['amount_paid']:.2f}",
                 p["invoice_number"] or "",
                 p["paid_date"].strftime("%d/%m/%Y") if isinstance(p.get("paid_date"),datetime) else "")
                for p in payments]
        if rows:
            self.make_table(card2, ["Tenant","Apt #","Amount","Invoice","Paid On"],
                            rows, [160,80,90,130,90]).pack(fill="x", padx=12, pady=(0,12))

    def _show_invoices(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Invoices")

        invoices = list(self.pay_ctrl.db["invoices"].find({"location": self.location}).sort("issued_date",-1).limit(50))
        rows = [(inv["invoice_number"], inv["tenant_name"], inv["apartment_number"],
                 f"£{inv['amount']:.2f}",
                 inv["due_date"].strftime("%d/%m/%Y") if isinstance(inv.get("due_date"),datetime) else "",
                 inv["issued_date"].strftime("%d/%m/%Y") if isinstance(inv.get("issued_date"),datetime) else "")
                for inv in invoices]
        tbl = self.make_table(f, ["Invoice #","Tenant","Apt #","Amount","Due","Issued"],
                              rows, [130,160,80,90,100,100])
        tbl.pack(fill="both", expand=True)

    def _show_payments(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Payment Records")

        top = ctk.CTkFrame(f, fg_color="transparent")
        top.pack(fill="x", pady=(0,12))
        status_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(top, values=["All","paid","pending","overdue","partial"],
                          variable=status_var, fg_color="#1c2333", button_color="#4e9af1",
                          command=lambda v: self._refresh_payments(f, v)).pack(side="left")

        self._refresh_payments(f, "All")

    def _refresh_payments(self, parent, status):
        for w in parent.winfo_children():
            if hasattr(w, "_pay_tbl"):
                w.destroy()
        s = None if status == "All" else status
        payments = self.pay_ctrl.get_all_payments(location=self.location, status=s)
        status_icons = {"paid":"✅","pending":"⏳","overdue":"🔴","partial":"🟡"}
        rows = [(p["tenant_name"], p["apartment_number"], f"£{p['amount']:.2f}",
                 f"£{p.get('amount_paid',0):.2f}",
                 status_icons.get(p["status"],"")+p["status"],
                 p["due_date"].strftime("%d/%m/%Y") if isinstance(p.get("due_date"),datetime) else "",
                 f"£{p.get('late_fee',0):.2f}")
                for p in payments]
        tbl = self.make_table(parent, ["Tenant","Apt","Due","Paid","Status","Due Date","Late Fee"],
                              rows, [150,70,80,80,110,90,80])
        tbl._pay_tbl = True
        tbl.pack(fill="both", expand=True)

    def _show_overdue(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Overdue Payments", "Payments past due date")

        payments = self.pay_ctrl.get_all_payments(location=self.location, status="overdue")
        pending  = [p for p in self.pay_ctrl.get_all_payments(location=self.location, status="pending")
                    if isinstance(p.get("due_date"),datetime) and p["due_date"] < datetime.utcnow()]

        all_overdue = payments + pending
        if not all_overdue:
            ctk.CTkLabel(f, text="✅ No overdue payments!", text_color="#68d391",
                         font=("Helvetica",16)).pack(pady=40)
            return

        for p in all_overdue:
            card = ctk.CTkFrame(f, fg_color="#2d1515", corner_radius=10)
            card.pack(fill="x", pady=4)
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=12)
            ctk.CTkLabel(row, text=p["tenant_name"], font=("Helvetica",14,"bold"),
                         text_color="white").pack(side="left")
            ctk.CTkLabel(row, text=f"£{p['amount']:.2f} overdue",
                         font=("Helvetica",13,"bold"), text_color="#fc8181").pack(side="right")
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(fill="x", padx=14, pady=(0,12))
            due = p["due_date"].strftime("%d/%m/%Y") if isinstance(p.get("due_date"),datetime) else ""
            for label, val in [("Apt",p["apartment_number"]),("Due",due),
                               ("Invoice",p.get("invoice_number",""))]:
                ctk.CTkLabel(info, text=f"{label}: {val}", font=("Helvetica",11),
                             text_color="#94a3b8").pack(side="left", padx=(0,16))
            ctk.CTkButton(info, text="Record Payment", width=130, height=30,
                          fg_color="#4e9af1", command=lambda pid=str(p["_id"]): self._record_payment_dialog(pid)
                          ).pack(side="right")

    def _record_payment_dialog(self, payment_id):
        dlg = ctk.CTkToplevel(self.content_area)
        dlg.title("Record Payment")
        dlg.geometry("400x300")
        dlg.grab_set()

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(form, text="Record Payment", font=("Helvetica",15,"bold")).pack(anchor="w",pady=(0,12))

        ctk.CTkLabel(form, text="Amount Paid (£)", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        amt_e = ctk.CTkEntry(form, placeholder_text="Amount received")
        amt_e.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Card Last 4 Digits", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        card_e = ctk.CTkEntry(form, placeholder_text="e.g. 4242")
        card_e.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Notes", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        notes_e = ctk.CTkEntry(form, placeholder_text="Optional notes")
        notes_e.pack(fill="x", pady=(2,10))

        msg = ctk.CTkLabel(form, text="", font=("Helvetica",11), text_color="#fc8181")
        msg.pack()

        def submit():
            try:
                amt = float(amt_e.get())
            except ValueError:
                msg.configure(text="Enter valid amount."); return
            ok, m = self.pay_ctrl.record_payment(payment_id, amt, card_e.get().strip(), notes_e.get().strip())
            msg.configure(text=m, text_color="#68d391" if ok else "#fc8181")
            if ok:
                dlg.after(1200, dlg.destroy)

        ctk.CTkButton(form, text="Record Payment", fg_color="#4e9af1", command=submit).pack(fill="x", pady=4)

    def _show_create_invoice(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Create Invoice / Payment Record")

        card = self.make_card(f)
        card.pack(fill="x")
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=16)

        tenants = self.ten_ctrl.get_all_tenants(self.location, "active")
        t_opts = [f"{t['full_name']}" for t in tenants]
        t_map  = {t["full_name"]: t for t in tenants}

        ctk.CTkLabel(form, text="Tenant *", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        t_var = ctk.StringVar(value=t_opts[0] if t_opts else "")
        ctk.CTkOptionMenu(form, values=t_opts or ["None"], variable=t_var,
                          fg_color="#1c2333", button_color="#4e9af1").pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Payment Type *", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        pt_var = ctk.StringVar(value="rent")
        ctk.CTkOptionMenu(form, values=["rent","deposit","early_termination_penalty","maintenance_charge","late_fee"],
                          variable=pt_var, fg_color="#1c2333", button_color="#4e9af1").pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Amount (£) *", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        amt_e = ctk.CTkEntry(form, placeholder_text="Amount")
        amt_e.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(form, text="Due Date *", font=("Helvetica",12), text_color="#94a3b8", anchor="w").pack(fill="x")
        due_e = ctk.CTkEntry(form, placeholder_text="YYYY-MM-DD")
        due_e.insert(0, (datetime.utcnow()+timedelta(days=7)).strftime("%Y-%m-%d"))
        due_e.pack(fill="x", pady=(2,10))

        msg = ctk.CTkLabel(form, text="", font=("Helvetica",11), text_color="#fc8181")
        msg.pack()

        def submit():
            from utils.validators import validate_date_format
            tn = t_var.get()
            if tn not in t_map:
                msg.configure(text="Select valid tenant."); return
            t_obj = t_map[tn]
            apts = self.apt_ctrl.get_all_apartments(self.location, "occupied")
            apt_obj = next((a for a in apts if a.get("current_tenant_id")==str(t_obj["_id"])), None)
            if not apt_obj:
                msg.configure(text="Tenant has no assigned apartment."); return
            lease = self.apt_ctrl.get_tenant_lease(str(t_obj["_id"]))
            if not lease:
                msg.configure(text="No active lease found."); return
            try:
                amount = float(amt_e.get())
            except ValueError:
                msg.configure(text="Enter valid amount."); return
            due_s = due_e.get().strip()
            if not validate_date_format(due_s):
                msg.configure(text="Invalid date format."); return
            due_dt = datetime.strptime(due_s, "%Y-%m-%d")
            _, err = self.pay_ctrl.create_payment(
                str(t_obj["_id"]), t_obj["full_name"], str(apt_obj["_id"]),
                apt_obj["apartment_number"], str(lease["_id"]),
                amount, due_dt, pt_var.get(), self.location, self.user["username"]
            )
            if err:
                msg.configure(text=err, text_color="#fc8181")
            else:
                msg.configure(text="Invoice created successfully!", text_color="#68d391")

        ctk.CTkButton(card, text="Create Invoice", fg_color="#4e9af1", hover_color="#2b6cb0",
                      height=42, command=submit).pack(padx=20, pady=(4,16), fill="x")

    def _show_reports(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.page_header(f, "Financial Reports")

        fin = self.rpt_ctrl.financial_report(self.location)

        # Pie chart
        card = self.make_card(f, "Payment Status Breakdown")
        card.pack(fill="x", pady=(0,16))
        labels = ["Collected","Pending","Overdue","Late Fees"]
        sizes  = [fin["collected"], fin["pending"], fin["overdue"], fin["late_fees"]]
        colors = ["#68d391","#f6ad55","#fc8181","#9f7aea"]
        sizes  = [max(s, 0) for s in sizes]
        if sum(sizes) > 0:
            fig, ax = plt.subplots(figsize=(5,4))
            fig.patch.set_facecolor("#1c2333")
            ax.set_facecolor("#1c2333")
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors,
                                              autopct="%1.1f%%", startangle=90,
                                              textprops={"color":"#e2e8f0","fontsize":10})
            for at in autotexts:
                at.set_color("white")
            ax.set_title("Payment Distribution", color="white", pad=10)
            plt.tight_layout()
            canvas = FigureCanvasTkAgg(fig, card)
            canvas.draw()
            canvas.get_tk_widget().pack(pady=(0,12))
            plt.close(fig)
