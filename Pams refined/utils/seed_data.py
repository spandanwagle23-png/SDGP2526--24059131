"""
Seed script to populate MongoDB with test data.
Run: python utils/seed_data.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

import bcrypt
from datetime import datetime, timedelta
from config.database import DatabaseConnection

def seed():
    db = DatabaseConnection.get_instance()

    # Clear existing
    for col in ["users","tenants","apartments","leases","payments","invoices",
                "maintenance_requests","complaints","locations"]:
        db[col].drop()
    print("Collections cleared.")

    # Locations
    locations = [
        {"city": "Bristol", "address": "10 Park St, Bristol", "created_by": "system", "created_at": datetime.utcnow()},
        {"city": "Cardiff", "address": "5 Queen St, Cardiff", "created_by": "system", "created_at": datetime.utcnow()},
        {"city": "London",  "address": "100 Oxford St, London", "created_by": "system", "created_at": datetime.utcnow()},
        {"city": "Manchester","address": "20 Deansgate, Manchester", "created_by": "system", "created_at": datetime.utcnow()},
    ]
    db["locations"].insert_many(locations)
    print("Locations seeded.")

    def hash_pw(pw):
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt())

    # Users
    users = [
        {"username":"manager1","password_hash":hash_pw("Manager@1"),"role":"manager","full_name":"Sarah Johnson","email":"sarah.johnson@paragon.com","phone":"07700900001","location":"Bristol","is_active":True,"created_by":"system","created_at":datetime.utcnow(),"updated_at":datetime.utcnow()},
        {"username":"admin_bristol","password_hash":hash_pw("Admin@1"),"role":"admin","full_name":"Tom Williams","email":"tom.w@paragon.com","phone":"07700900002","location":"Bristol","is_active":True,"created_by":"system","created_at":datetime.utcnow(),"updated_at":datetime.utcnow()},
        {"username":"admin_london","password_hash":hash_pw("Admin@2"),"role":"admin","full_name":"Emma Davis","email":"emma.d@paragon.com","phone":"07700900003","location":"London","is_active":True,"created_by":"system","created_at":datetime.utcnow(),"updated_at":datetime.utcnow()},
        {"username":"frontdesk1","password_hash":hash_pw("Front@1"),"role":"front_desk","full_name":"Jack Brown","email":"jack.b@paragon.com","phone":"07700900004","location":"Bristol","is_active":True,"created_by":"system","created_at":datetime.utcnow(),"updated_at":datetime.utcnow()},
        {"username":"finance1","password_hash":hash_pw("Finance@1"),"role":"finance_manager","full_name":"Lisa Green","email":"lisa.g@paragon.com","phone":"07700900005","location":"Bristol","is_active":True,"created_by":"system","created_at":datetime.utcnow(),"updated_at":datetime.utcnow()},
        {"username":"maint1","password_hash":hash_pw("Maint@1"),"role":"maintenance_staff","full_name":"Bob Taylor","email":"bob.t@paragon.com","phone":"07700900006","location":"Bristol","is_active":True,"created_by":"system","created_at":datetime.utcnow(),"updated_at":datetime.utcnow()},
    ]
    user_result = db["users"].insert_many(users)
    print(f"Users seeded: {len(users)}")

    # Apartments
    apartments = []
    apt_types = [("Studio",1,400,450),("1-Bedroom",1,600,650),("2-Bedroom",2,900,1000),("3-Bedroom",3,1200,1400)]
    apt_counter = 1
    for loc in ["Bristol","Cardiff","London","Manchester"]:
        for floor in [1,2,3]:
            for i, (t, rooms, rent_min, rent_max) in enumerate(apt_types):
                import random
                apartments.append({
                    "apartment_number": f"{loc[:2].upper()}-{floor}0{i+1}",
                    "location": loc,
                    "apartment_type": t,
                    "monthly_rent": random.randint(rent_min, rent_max),
                    "num_rooms": rooms,
                    "floor": floor,
                    "size_sqft": random.randint(300, 1200),
                    "amenities": ["parking","gym"] if random.random()>0.5 else ["parking"],
                    "status": "available",
                    "current_tenant_id": None,
                    "created_by": "system",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
    apt_result = db["apartments"].insert_many(apartments)
    apt_ids = apt_result.inserted_ids
    print(f"Apartments seeded: {len(apartments)}")

    # Tenants + Leases + Payments
    tenant_data = [
        ("AB123456C","Alice Smith","07911111001","alice@email.com","Teacher","John Doe","2-Bedroom",12,"1990-05-15","07911000001","Bristol"),
        ("CD234567D","Michael Jones","07911111002","michael@email.com","Engineer","Jane Doe","1-Bedroom",6,"1985-08-22","07911000002","Bristol"),
        ("EF345678A","Priya Patel","07911111003","priya@email.com","Nurse","David Lee","3-Bedroom",12,"1992-03-10","07911000003","Bristol"),
        ("GH456789B","James Wilson","07911111004","james@email.com","Developer","Sarah Fox","Studio",6,"1995-11-20","07911000004","Bristol"),
        ("IJ567890C","Fatima Hassan","07911111005","fatima@email.com","Accountant","Mark Hill","2-Bedroom",12,"1988-07-04","07911000005","London"),
    ]
    import random, string

    def gen_inv():
        return "INV-" + "".join(random.choices(string.ascii_uppercase+string.digits,k=8))

    bristol_apts = [a for a in apt_ids[:len(apartments)] if apartments[apt_ids.index(a)]["location"] in ["Bristol","London"]]
    available_apts = list(db["apartments"].find({"status":"available"}))

    tenant_user_passwords = []
    for idx, (ni, name, phone, email, occ, ref, apt_req, lease_mo, dob, emerg, loc) in enumerate(tenant_data):
        # Insert tenant
        t_doc = {
            "ni_number":ni,"full_name":name,"phone":phone,"email":email,
            "occupation":occ,"references":ref,"apartment_requirements":apt_req,
            "lease_period":lease_mo,"date_of_birth":dob,"emergency_contact":emerg,
            "location":loc,"status":"active","registered_by":"frontdesk1",
            "created_at":datetime.utcnow(),"updated_at":datetime.utcnow()
        }
        t_id = db["tenants"].insert_one(t_doc).inserted_id

        # Assign apartment
        apts_at_loc = [a for a in available_apts if a["location"]==loc and a["status"]=="available"]
        if not apts_at_loc:
            continue
        apt = apts_at_loc[0]
        available_apts.remove(apt)
        apt_id = apt["_id"]
        start = datetime.utcnow() - timedelta(days=random.randint(30,180))
        end = start + timedelta(days=lease_mo*30)
        lease_doc = {
            "tenant_id":str(t_id),"tenant_name":name,"apartment_id":str(apt_id),
            "apartment_number":apt["apartment_number"],"location":loc,
            "start_date":start,"end_date":end,"monthly_rent":apt["monthly_rent"],
            "deposit_amount":apt["monthly_rent"]*2,"status":"active","early_termination":None,
            "created_by":"frontdesk1","created_at":datetime.utcnow(),"updated_at":datetime.utcnow()
        }
        lease_id = db["leases"].insert_one(lease_doc).inserted_id
        db["apartments"].update_one({"_id":apt_id},{"$set":{"status":"occupied","current_tenant_id":str(t_id)}})

        # Payments (last 6 months)
        for mo in range(6):
            due = start + timedelta(days=30*(mo+1))
            is_paid = mo < 5
            is_late = mo == 2
            inv_num = gen_inv()
            pay_doc = {
                "tenant_id":str(t_id),"tenant_name":name,"apartment_id":str(apt_id),
                "apartment_number":apt["apartment_number"],"lease_id":str(lease_id),
                "amount":apt["monthly_rent"],"amount_paid":apt["monthly_rent"] if is_paid else 0,
                "due_date":due,"paid_date":due+timedelta(days=5 if is_late else 0) if is_paid else None,
                "payment_type":"rent","status":"paid" if is_paid else "pending",
                "invoice_number":inv_num,"card_last4":"4242" if is_paid else None,
                "location":loc,"late_fee":apt["monthly_rent"]*0.05 if is_late else 0,
                "notes":"","created_by":"system","created_at":due,"updated_at":due
            }
            pay_id = db["payments"].insert_one(pay_doc).inserted_id
            db["invoices"].insert_one({
                "invoice_number":inv_num,"payment_id":str(pay_id),"tenant_id":str(t_id),
                "tenant_name":name,"apartment_number":apt["apartment_number"],
                "amount":apt["monthly_rent"],"due_date":due,"location":loc,
                "issued_date":due,"created_at":due
            })

        # Create tenant login user
        uname = name.split()[0].lower() + str(idx+1)
        t_user = {
            "username":uname,"password_hash":hash_pw("Tenant@1"),"role":"tenant",
            "full_name":name,"email":email,"phone":phone,"location":loc,
            "tenant_id":str(t_id),"apartment_id":str(apt_id),"lease_id":str(lease_id),
            "is_active":True,"created_by":"frontdesk1",
            "created_at":datetime.utcnow(),"updated_at":datetime.utcnow()
        }
        db["users"].insert_one(t_user)
        tenant_user_passwords.append((uname,"Tenant@1",name))

    print(f"Tenants seeded: {len(tenant_data)}")

    # Maintenance requests
    main_requests = [
        ("Broken Boiler","The boiler has stopped working and there is no hot water.","High"),
        ("Leaking Tap","The kitchen tap is leaking and wasting water.","Medium"),
        ("Broken Window Lock","Bedroom window lock is broken.","High"),
        ("Mould on Wall","There is mould forming on the bathroom wall.","Low"),
        ("Faulty Lights","The lights in the living room keep flickering.","Medium"),
    ]
    tenants = list(db["tenants"].find())
    for i, (title, desc, priority) in enumerate(main_requests):
        t = tenants[i % len(tenants)]
        apt = db["apartments"].find_one({"current_tenant_id":str(t["_id"])})
        if not apt:
            continue
        db["maintenance_requests"].insert_one({
            "tenant_id":str(t["_id"]),"tenant_name":t["full_name"],
            "apartment_id":str(apt["_id"]),"apartment_number":apt["apartment_number"],
            "location":t["location"],"issue_title":title,"issue_description":desc,
            "priority":priority,"status":"submitted" if i>2 else "resolved",
            "assigned_to":"Bob Taylor" if i<=2 else None,
            "scheduled_date":datetime.utcnow() if i<=2 else None,
            "scheduled_time":"10:00 AM" if i<=2 else None,
            "resolution_notes":"Issue resolved successfully." if i<=2 else None,
            "time_taken_hours":2.5 if i<=2 else None,
            "cost":150 if i<=2 else 0,
            "reported_by":t["full_name"],"created_at":datetime.utcnow()-timedelta(days=10-i),
            "updated_at":datetime.utcnow(),"resolved_at":datetime.utcnow() if i<=2 else None
        })
    print("Maintenance requests seeded.")

    # Complaints
    complaints = [
        ("noise","Noise Complaint","Neighbour is making loud noise after midnight."),
        ("facility","Gym Equipment Broken","The treadmill in the gym is broken."),
        ("billing","Invoice Error","I was charged twice for this month's rent."),
    ]
    for i, (ctype, subj, desc) in enumerate(complaints):
        t = tenants[i % len(tenants)]
        apt = db["apartments"].find_one({"current_tenant_id":str(t["_id"])})
        if not apt:
            continue
        db["complaints"].insert_one({
            "tenant_id":str(t["_id"]),"tenant_name":t["full_name"],
            "apartment_id":str(apt["_id"]),"apartment_number":apt["apartment_number"],
            "location":t["location"],"complaint_type":ctype,"subject":subj,"description":desc,
            "status":"open","resolution_notes":None,"reported_by":t["full_name"],
            "created_at":datetime.utcnow()-timedelta(days=5-i),
            "updated_at":datetime.utcnow(),"resolved_at":None
        })
    print("Complaints seeded.")

    print("\n=== SEED COMPLETE ===")
    print("\nStaff Login Credentials:")
    print("  manager1       / Manager@1  (Manager)")
    print("  admin_bristol  / Admin@1    (Admin - Bristol)")
    print("  admin_london   / Admin@2    (Admin - London)")
    print("  frontdesk1     / Front@1    (Front Desk - Bristol)")
    print("  finance1       / Finance@1  (Finance Manager - Bristol)")
    print("  maint1         / Maint@1    (Maintenance Staff - Bristol)")
    print("\nTenant Login Credentials:")
    for uname, pw, name in tenant_user_passwords:
        print(f"  {uname:<15} / {pw}  ({name})")

if __name__ == "__main__":
    seed()
