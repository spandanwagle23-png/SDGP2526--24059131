import bcrypt
from config.database import DatabaseConnection

class AuthController:
    def __init__(self):
        self.db = DatabaseConnection.get_instance()
        self.users = self.db["users"]

    def login(self, username, password):
        user = self.users.find_one({"username": username, "is_active": True})
        if not user:
            return None, "Invalid username or password."
        if bcrypt.checkpw(password.encode(), user["password_hash"]):
            return user, None
        return None, "Invalid username or password."

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def change_password(self, user_id, old_password, new_password):
        from bson import ObjectId
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return False, "User not found."
        if not bcrypt.checkpw(old_password.encode(), user["password_hash"]):
            return False, "Current password is incorrect."
        new_hash = self.hash_password(new_password)
        self.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"password_hash": new_hash}})
        return True, "Password changed successfully."
