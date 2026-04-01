====================================================
  PARAGON APARTMENT MANAGEMENT SYSTEM (PAMS)
  Advanced Software Development - UWE Bristol
====================================================

SETUP INSTRUCTIONS
------------------

1. SETUP VENV & INSTALL DEPENDENCIES
   python -m venv venv 
   if (CMD): venv\Scripts\activate
   if (PS): .\venv\Scripts\Activate.ps1 
   pip install -r requirements.txt

2. CONFIGURE DATABASE
   - Create .env file in root of directory
   - Open the .env file
   - Replace "your_mongodb_atlas_uri_here" with your MongoDB Atlas URI:
     MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
     DB_NAME=pams_db

3. SEED THE DATABASE (Required before first run)
   python utils/seed_data.py
   (This creates test data, apartments, and user accounts)

4. RUN THE APPLICATION
   python main.py


LOGIN CREDENTIALS (after seeding)
-----------------------------------

Staff Accounts:
  Username: manager1        Password: Manager@1   Role: Manager
  Username: admin_bristol   Password: Admin@1     Role: Admin (Bristol)
  Username: admin_london    Password: Admin@2     Role: Admin (London)
  Username: frontdesk1      Password: Front@1     Role: Front Desk (Bristol)
  Username: finance1        Password: Finance@1   Role: Finance Manager (Bristol)
  Username: maint1          Password: Maint@1     Role: Maintenance Staff (Bristol)

Tenant Accounts (created automatically during seeding):
  Username: alice1          Password: Tenant@1    (Bristol)
  Username: michael2        Password: Tenant@1    (Bristol)
  Username: priya3          Password: Tenant@1    (Bristol)
  Username: james4          Password: Tenant@1    (Bristol)
  Username: fatima5         Password: Tenant@1    (London)


SYSTEM FEATURES
---------------

MANAGER:
  - System-wide occupancy overview
  - Performance reports across all cities
  - Add new city/branch locations

ADMINISTRATOR (per location):
  - Manage staff user accounts
  - Register and manage apartments
  - View and track lease agreements
  - Financial and maintenance reports

FRONT DESK STAFF:
  - Register new tenants
  - Tenant lookup and editing
  - Assign apartments / create leases
  - Log maintenance requests
  - Log tenant complaints

FINANCE MANAGER:
  - View and manage all invoices
  - Record payments
  - Manage overdue payments
  - Create new invoices
  - Financial reports with charts

MAINTENANCE STAFF:
  - View assigned tasks
  - Assign and schedule requests
  - Resolve requests with cost/time logging
  - Priority-based queue

TENANT PORTAL:
  - View personal payment history
  - Make emulated card payments
  - Submit repair requests
  - Track repair progress
  - Submit complaints
  - Payment history charts
  - Neighbour payment comparison
  - Late payment history chart


PROJECT STRUCTURE
-----------------
PAMS/
├── main.py                   ← Application entry point
├── .env                      ← MongoDB URI config (fill this in!)
├── requirements.txt
├── README.txt
├── config/
│   └── database.py           ← MongoDB Atlas connection
├── models/
│   ├── user_model.py
│   ├── tenant_model.py
│   ├── apartment_model.py
│   ├── lease_model.py
│   ├── payment_model.py
│   ├── maintenance_model.py
│   └── complaint_model.py
├── controllers/
│   ├── auth_controller.py
│   ├── user_controller.py
│   ├── tenant_controller.py
│   ├── apartment_controller.py
│   ├── payment_controller.py
│   ├── maintenance_controller.py
│   ├── complaint_controller.py
│   └── report_controller.py
├── views/
│   ├── base_dashboard.py     ← Shared sidebar layout
│   ├── login_view.py
│   ├── manager_dashboard.py
│   ├── admin_dashboard.py
│   ├── frontdesk_dashboard.py
│   ├── finance_dashboard.py
│   ├── maintenance_dashboard.py
│   └── tenant_dashboard.py
└── utils/
    ├── validators.py
    └── seed_data.py


DEPENDENCIES (requirements.txt)
--------------------------------
  customtkinter   - Modern dark UI framework
  pymongo         - MongoDB Atlas driver
  python-dotenv   - .env file loading
  bcrypt          - Secure password hashing
  matplotlib      - Payment charts and graphs
  Pillow          - Image support
  dnspython       - MongoDB Atlas DNS resolution


SECURITY FEATURES
-----------------
  - Passwords hashed with bcrypt
  - Role-based access control (5 staff roles + tenant)
  - Location-scoped data access for admins
  - Input validation (NI format, email, phone, dates)
  - Password complexity requirements
  - Emulated card validation (Luhn-like checks)


NOTES
-----
  - This is a DESKTOP application (CustomTkinter + Python)
  - Web development is NOT used (as per assessment requirements)
  - Payment processing is EMULATED — no real charges
  - MongoDB Atlas collections: users, tenants, apartments, leases,
    payments, invoices, maintenance_requests, complaints, locations
    
name of the student who have written this code =>
Muhammad Khan 24050247
Tasniah Rashid Mila
24042408
Muhammad azan ishtiaq
24050946
spandan wagle
24059131
Mahtab Bin Lokman
 24038250