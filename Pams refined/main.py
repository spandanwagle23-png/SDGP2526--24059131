"""
Paragon Apartment Management System (PAMS)
==========================================
Main entry point.

Usage:
    python main.py

Make sure to:
1. Set MONGO_URI in .env file
2. Run seed: python utils/seed_data.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PAMSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Paragon Apartment Management System (PAMS)")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        try:
            from config.database import DatabaseConnection
            DatabaseConnection.get_instance()
            print("[DB] Connected to MongoDB.")
        except Exception as e:
            print(f"[DB ERROR] {e}")
            self._show_db_error(str(e))
            return

        self.show_login()

    def show_login(self):
        self._clear()
        from views.login_view import LoginView
        LoginView(self).pack(fill="both", expand=True)

    def show_dashboard(self, user):
        self._clear()
        role = user.get("role")
        try:
            if role == "manager":
                from views.manager_dashboard import ManagerDashboard
                ManagerDashboard(self, user).pack(fill="both", expand=True)
            elif role == "admin":
                from views.admin_dashboard import AdminDashboard
                AdminDashboard(self, user).pack(fill="both", expand=True)
            elif role == "front_desk":
                from views.frontdesk_dashboard import FrontdeskDashboard
                FrontdeskDashboard(self, user).pack(fill="both", expand=True)
            elif role == "finance_manager":
                from views.finance_dashboard import FinanceDashboard
                FinanceDashboard(self, user).pack(fill="both", expand=True)
            elif role == "maintenance_staff":
                from views.maintenance_dashboard import MaintenanceDashboard
                MaintenanceDashboard(self, user).pack(fill="both", expand=True)
            elif role == "tenant":
                from views.tenant_dashboard import TenantDashboard
                TenantDashboard(self, user).pack(fill="both", expand=True)
            else:
                import customtkinter as ctk
                ctk.CTkLabel(self, text=f"Unknown role: {role}", text_color="red"
                             ).pack(expand=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            import customtkinter as ctk
            ctk.CTkLabel(self, text=f"Error loading dashboard: {e}", text_color="red",
                         wraplength=800).pack(expand=True, padx=40)

    def _clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def _show_db_error(self, msg):
        import customtkinter as ctk
        ctk.CTkLabel(self, text="❌ Database Connection Failed", font=("Helvetica",20,"bold"),
                     text_color="#fc8181").pack(pady=(100,10))
        ctk.CTkLabel(self, text=msg, font=("Helvetica",12), text_color="#94a3b8",
                     wraplength=600).pack(pady=10)
        ctk.CTkLabel(self, text="Please check your MONGO_URI in the .env file.",
                     font=("Helvetica",13), text_color="#f6ad55").pack(pady=10)

    def _on_close(self):
        self.destroy()
        sys.exit(0)


if __name__ == "__main__":
    app = PAMSApp()
    app.mainloop()
