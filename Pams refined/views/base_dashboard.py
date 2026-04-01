import customtkinter as ctk
from datetime import datetime

class BaseDashboard(ctk.CTkFrame):
    """
    Shared base class for all role dashboards.
    Provides a sidebar + content area layout.
    """
    SIDEBAR_COLOR = "#111827"
    CONTENT_COLOR = "#0d1117"
    CARD_COLOR = "#1c2333"
    ACCENT = "#4e9af1"
    TEXT_PRIMARY = "#e2e8f0"
    TEXT_SECONDARY = "#94a3b8"

    def __init__(self, master, user, nav_items):
        super().__init__(master, fg_color="transparent")
        self.master = master
        self.user = user
        self.nav_items = nav_items  # list of (label, icon, callback)
        self.current_frame = None
        self._build_layout()

    def _build_layout(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, fg_color=self.SIDEBAR_COLOR, corner_radius=0, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # Content area
        self.content_area = ctk.CTkFrame(self, fg_color=self.CONTENT_COLOR, corner_radius=0)
        self.content_area.pack(side="right", fill="both", expand=True)

    def _build_sidebar(self):
        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="#0d1220", height=70, corner_radius=0)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)
        ctk.CTkLabel(logo_frame, text="PAMS", font=("Helvetica", 22, "bold"),
                     text_color=self.ACCENT).pack(pady=10)

        # User info card
        user_card = ctk.CTkFrame(self.sidebar, fg_color="#161f35", corner_radius=8)
        user_card.pack(fill="x", padx=12, pady=(12, 8))
        role_labels = {
            "admin": "Administrator", "manager": "Manager",
            "front_desk": "Front-Desk Staff", "finance_manager": "Finance Manager",
            "maintenance_staff": "Maintenance Staff", "tenant": "Tenant"
        }
        ctk.CTkLabel(user_card, text=self.user.get("full_name","User"),
                     font=("Helvetica", 13, "bold"), text_color=self.TEXT_PRIMARY,
                     anchor="w").pack(fill="x", padx=10, pady=(8,1))
        ctk.CTkLabel(user_card, text=role_labels.get(self.user.get("role",""), "User"),
                     font=("Helvetica", 11), text_color=self.ACCENT, anchor="w").pack(fill="x", padx=10)
        ctk.CTkLabel(user_card, text=f"📍 {self.user.get('location','N/A')}",
                     font=("Helvetica", 11), text_color=self.TEXT_SECONDARY, anchor="w"
                     ).pack(fill="x", padx=10, pady=(1,8))

        # Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color="#2d3748").pack(fill="x", padx=12, pady=4)

        # Nav items
        self.nav_buttons = {}
        for label, icon, callback in self.nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}  {label}",
                font=("Helvetica", 13),
                fg_color="transparent",
                text_color=self.TEXT_SECONDARY,
                hover_color="#1e2d45",
                anchor="w",
                height=40,
                corner_radius=8,
                command=lambda l=label, cb=callback: self._nav_click(l, cb)
            )
            btn.pack(fill="x", padx=8, pady=2)
            self.nav_buttons[label] = btn

        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)

        # Logout
        ctk.CTkFrame(self.sidebar, height=1, fg_color="#2d3748").pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(
            self.sidebar,
            text="  🚪  Logout",
            font=("Helvetica", 13),
            fg_color="transparent",
            text_color="#fc8181",
            hover_color="#2d1515",
            anchor="w",
            height=40,
            corner_radius=8,
            command=self._logout
        ).pack(fill="x", padx=8, pady=(0,12))

    def _nav_click(self, label, callback):
        for lbl, btn in self.nav_buttons.items():
            if lbl == label:
                btn.configure(fg_color="#1e3a5f", text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=self.TEXT_SECONDARY)
        self._clear_content()
        callback()

    def _clear_content(self):
        for w in self.content_area.winfo_children():
            w.destroy()

    def show_page(self, frame_class, **kwargs):
        self._clear_content()
        frame = frame_class(self.content_area, self.user, **kwargs)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.current_frame = frame

    def _logout(self):
        self.master.show_login()

    def navigate_to(self, label):
        """Programmatically click a nav item by label."""
        for lbl, icon, cb in self.nav_items:
            if lbl == label:
                self._nav_click(lbl, cb)
                break

    # --- Shared widget helpers ---
    @staticmethod
    def make_card(parent, title=None, **kwargs):
        card = ctk.CTkFrame(parent, fg_color=BaseDashboard.CARD_COLOR,
                            corner_radius=10, **kwargs)
        if title:
            ctk.CTkLabel(card, text=title, font=("Helvetica", 14, "bold"),
                         text_color=BaseDashboard.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(12,4))
        return card

    @staticmethod
    def stat_card(parent, title, value, subtitle="", color="#4e9af1"):
        card = ctk.CTkFrame(parent, fg_color=BaseDashboard.CARD_COLOR, corner_radius=10)
        ctk.CTkLabel(card, text=title, font=("Helvetica", 12), text_color=BaseDashboard.TEXT_SECONDARY
                     ).pack(anchor="w", padx=14, pady=(12,2))
        ctk.CTkLabel(card, text=str(value), font=("Helvetica", 26, "bold"), text_color=color
                     ).pack(anchor="w", padx=14)
        if subtitle:
            ctk.CTkLabel(card, text=subtitle, font=("Helvetica", 11), text_color=BaseDashboard.TEXT_SECONDARY
                         ).pack(anchor="w", padx=14, pady=(0,12))
        return card

    @staticmethod
    def make_table(parent, columns, data, col_widths=None):
        """Simple scrollable table widget."""
        frame = ctk.CTkScrollableFrame(parent, fg_color="transparent", height=700)

        # Header
        header = ctk.CTkFrame(frame, fg_color="#1e3a5f", corner_radius=6)
        header.pack(fill="x", pady=(0,2))
        for i, col in enumerate(columns):
            w = col_widths[i] if col_widths else 120
            ctk.CTkLabel(header, text=col, font=("Helvetica", 12, "bold"),
                         text_color="#90cdf4", width=w, anchor="w"
                         ).grid(row=0, column=i, padx=8, pady=8, sticky="w")

        # Rows
        for ri, row in enumerate(data):
            bg = "#161f35" if ri % 2 == 0 else "#1a2540"
            row_frame = ctk.CTkFrame(frame, fg_color=bg, corner_radius=4)
            row_frame.pack(fill="x", pady=1)
            for ci, cell in enumerate(row):
                w = col_widths[ci] if col_widths else 120
                ctk.CTkLabel(row_frame, text=str(cell), font=("Helvetica", 11),
                             text_color=BaseDashboard.TEXT_PRIMARY, width=w, anchor="w"
                             ).grid(row=0, column=ci, padx=8, pady=7, sticky="w")
        return frame

    @staticmethod
    def page_header(parent, title, subtitle=""):
        ctk.CTkLabel(parent, text=title, font=("Helvetica", 22, "bold"),
                     text_color="white").pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(parent, text=subtitle, font=("Helvetica", 13),
                         text_color=BaseDashboard.TEXT_SECONDARY).pack(anchor="w", pady=(2,0))
        ctk.CTkFrame(parent, height=1, fg_color="#2d3748").pack(fill="x", pady=12)

    @staticmethod
    def show_message(parent, msg, color="#4e9af1"):
        popup = ctk.CTkToplevel(parent)
        popup.title("PAMS")
        popup.geometry("380x160")
        popup.resizable(False, False)
        popup.grab_set()
        ctk.CTkLabel(popup, text=msg, font=("Helvetica", 13), text_color=color,
                     wraplength=340).pack(expand=True, pady=20, padx=20)
        ctk.CTkButton(popup, text="OK", fg_color="#4e9af1", command=popup.destroy
                      ).pack(pady=(0,20))
