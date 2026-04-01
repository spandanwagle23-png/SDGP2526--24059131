from datetime import datetime, timedelta
from bson import ObjectId
import random, string
from config.database import DatabaseConnection
from models.payment_model import payment_schema, invoice_schema

class PaymentController:
    def __init__(self):
        self.db = DatabaseConnection.get_instance()
        self.payments = self.db["payments"]
        self.invoices = self.db["invoices"]

    def _gen_invoice_number(self):
        return "INV-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def create_payment(self, tenant_id, tenant_name, apartment_id, apartment_number,
                       lease_id, amount, due_date, payment_type, location, created_by):
        doc = payment_schema(tenant_id, tenant_name, apartment_id, apartment_number,
                             lease_id, amount, due_date, payment_type, location, created_by)
        inv_num = self._gen_invoice_number()
        doc["invoice_number"] = inv_num
        result = self.payments.insert_one(doc)
        # Create invoice record
        inv_doc = invoice_schema(result.inserted_id, tenant_id, tenant_name,
                                 apartment_number, amount, due_date, inv_num, location)
        self.invoices.insert_one(inv_doc)
        return str(result.inserted_id), None

    def record_payment(self, payment_id, amount_paid, card_last4=None, notes=""):
        payment = self.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            return False, "Payment not found."
        due = payment["due_date"]
        late_fee = 0
        if isinstance(due, datetime) and datetime.utcnow() > due:
            late_fee = round(payment["amount"] * 0.05, 2)  # 5% late fee
        paid_date = datetime.utcnow()
        new_status = "paid" if amount_paid >= payment["amount"] else "partial"
        self.payments.update_one({"_id": ObjectId(payment_id)}, {"$set": {
            "amount_paid": amount_paid,
            "paid_date": paid_date,
            "status": new_status,
            "late_fee": late_fee,
            "card_last4": card_last4,
            "notes": notes,
            "updated_at": datetime.utcnow()
        }})
        return True, f"Payment recorded. {'Late fee applied: £' + str(late_fee) if late_fee else ''}"

    def get_payments_by_tenant(self, tenant_id):
        return list(self.payments.find({"tenant_id": str(tenant_id)}).sort("created_at", -1))

    def get_overdue_payments(self, location=None):
        query = {"status": {"$in": ["pending", "partial"]}, "due_date": {"$lt": datetime.utcnow()}}
        if location:
            query["location"] = location
        results = list(self.payments.find(query))
        # Mark as overdue
        for p in results:
            self.payments.update_one({"_id": p["_id"]}, {"$set": {"status": "overdue"}})
        return list(self.payments.find({**query, "status": "overdue"} if not location else {**query, "location": location, "status": "overdue"}))

    def get_all_payments(self, location=None, status=None, tenant_id=None):
        query = {}
        if location:
            query["location"] = location
        if status:
            query["status"] = status
        if tenant_id:
            query["tenant_id"] = str(tenant_id)
        return list(self.payments.find(query).sort("due_date", -1))

    def get_financial_summary(self, location=None):
        query = {}
        if location:
            query["location"] = location
        all_payments = list(self.payments.find(query))
        total_due = sum(p["amount"] for p in all_payments)
        collected = sum(p.get("amount_paid", 0) for p in all_payments if p["status"] in ["paid", "partial"])
        pending = sum(p["amount"] for p in all_payments if p["status"] in ["pending", "partial"])
        overdue = sum(p["amount"] for p in all_payments if p["status"] == "overdue")
        late_fees = sum(p.get("late_fee", 0) for p in all_payments)
        return {
            "total_due": round(total_due, 2),
            "collected": round(collected, 2),
            "pending": round(pending, 2),
            "overdue": round(overdue, 2),
            "late_fees": round(late_fees, 2)
        }

    def get_neighbor_payments(self, tenant_id, apartment_id):
        """Get payment summary of neighbours in same building."""
        apt = self.db["apartments"].find_one({"_id": ObjectId(apartment_id)})
        if not apt:
            return []
        location = apt["location"]
        apt_num_prefix = apt["apartment_number"][:2] if len(apt["apartment_number"]) > 2 else apt["apartment_number"][0]
        # Get apartments at same location (neighbours)
        neighbors = list(self.db["apartments"].find({
            "location": location,
            "status": "occupied",
            "_id": {"$ne": ObjectId(apartment_id)}
        }).limit(5))
        result = []
        for n in neighbors:
            payments = list(self.payments.find({"apartment_id": str(n["_id"])}).sort("created_at", -1).limit(6))
            paid = sum(p.get("amount_paid", 0) for p in payments if p["status"] == "paid")
            pending = sum(p["amount"] for p in payments if p["status"] in ["pending", "overdue"])
            result.append({
                "apartment_number": n["apartment_number"],
                "paid": paid,
                "pending": pending
            })
        # Add current tenant
        my_payments = list(self.payments.find({"tenant_id": str(tenant_id)}).sort("created_at", -1).limit(6))
        my_paid = sum(p.get("amount_paid", 0) for p in my_payments if p["status"] == "paid")
        my_pending = sum(p["amount"] for p in my_payments if p["status"] in ["pending", "overdue"])
        result.insert(0, {"apartment_number": apt["apartment_number"] + " (You)", "paid": my_paid, "pending": my_pending})
        return result

    def validate_card(self, card_number, expiry, cvv, name):
        """Basic card validation (emulated - no real processing)."""
        card_number = card_number.replace(" ", "")
        if not card_number.isdigit() or len(card_number) not in [15, 16]:
            return False, "Invalid card number."
        if not expiry or len(expiry) != 5 or expiry[2] != "/":
            return False, "Invalid expiry (MM/YY)."
        month, year = expiry.split("/")
        if not month.isdigit() or not year.isdigit():
            return False, "Invalid expiry."
        now = datetime.utcnow()
        exp_year = 2000 + int(year)
        exp_month = int(month)
        if exp_year < now.year or (exp_year == now.year and exp_month < now.month):
            return False, "Card has expired."
        if not cvv.isdigit() or len(cvv) not in [3, 4]:
            return False, "Invalid CVV."
        if not name.strip():
            return False, "Cardholder name required."
        return True, card_number[-4:]
