import customtkinter as ctk
from controllers.auth_controller import AuthController

class LoginView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.master = master
        self.auth = AuthController()
        self._build()

    def _build(self):
        # Left decorative panel
        left = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=0)
        left.place(relx=0, rely=0, relwidth=0.45, relheight=1)

        ctk.CTkLabel(left, text="PAMS", font=("Helvetica", 52, "bold"),
                     text_color="#4e9af1").place(relx=0.5, rely=0.38, anchor="center")
        ctk.CTkLabel(left, text="Paragon Apartment\nManagement System",
                     font=("Helvetica", 16), text_color="#a0aec0", justify="center"
                     ).place(relx=0.5, rely=0.50, anchor="center")
        ctk.CTkLabel(left, text="Bristol · Cardiff · London · Manchester",
                     font=("Helvetica", 11), text_color="#718096"
                     ).place(relx=0.5, rely=0.60, anchor="center")

        # Right login panel
        right = ctk.CTkFrame(self, fg_color="#0f0f1a", corner_radius=0)
        right.place(relx=0.45, rely=0, relwidth=0.55, relheight=1)

        form = ctk.CTkFrame(right, fg_color="transparent")
        form.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.7)

        ctk.CTkLabel(form, text="Sign In", font=("Helvetica", 28, "bold"),
                     text_color="white").pack(pady=(0, 6))
        ctk.CTkLabel(form, text="Enter your credentials to continue",
                     font=("Helvetica", 13), text_color="#718096").pack(pady=(0, 30))

        # Username
        ctk.CTkLabel(form, text="Username", font=("Helvetica", 13), text_color="#a0aec0",
                     anchor="w").pack(fill="x")
        self.username_entry = ctk.CTkEntry(form, height=44, placeholder_text="Enter username",
                                           font=("Helvetica", 13))
        self.username_entry.pack(fill="x", pady=(4, 16))

        # Password
        ctk.CTkLabel(form, text="Password", font=("Helvetica", 13), text_color="#a0aec0",
                     anchor="w").pack(fill="x")
        self.password_entry = ctk.CTkEntry(form, height=44, placeholder_text="Enter password",
                                           show="•", font=("Helvetica", 13))
        self.password_entry.pack(fill="x", pady=(4, 6))

        # Show password
        self.show_pw = ctk.CTkCheckBox(form, text="Show password", font=("Helvetica", 12),
                                       text_color="#a0aec0", command=self._toggle_pw)
        self.show_pw.pack(anchor="w", pady=(0, 20))

        self.error_label = ctk.CTkLabel(form, text="", font=("Helvetica", 12),
                                        text_color="#fc8181")
        self.error_label.pack(pady=(0, 8))

        login_btn = ctk.CTkButton(form, text="Sign In", height=46, font=("Helvetica", 14, "bold"),
                                  fg_color="#4e9af1", hover_color="#2b6cb0",
                                  command=self._login)
        login_btn.pack(fill="x")

        self.password_entry.bind("<Return>", lambda e: self._login())
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())

        ctk.CTkLabel(right, text="© 2025 Paragon Apartment Management",
                     font=("Helvetica", 10), text_color="#4a5568"
                     ).place(relx=0.5, rely=0.95, anchor="center")

    def _toggle_pw(self):
        self.password_entry.configure(show="" if self.show_pw.get() else "•")

    def _login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            self.error_label.configure(text="Please enter username and password.")
            return
        self.error_label.configure(text="Signing in...")
        self.update()
        user, error = self.auth.login(username, password)
        if error:
            self.error_label.configure(text=error)
        else:
            self.master.show_dashboard(user)
