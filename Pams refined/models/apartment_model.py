from datetime import datetime

APARTMENT_TYPES = ["Studio", "1-Bedroom", "2-Bedroom", "3-Bedroom", "4-Bedroom", "Penthouse"]
APARTMENT_STATUS = ["available", "occupied", "maintenance", "unavailable"]

def apartment_schema(apartment_number, location, apartment_type, monthly_rent,
                     num_rooms, floor, size_sqft, amenities, created_by):
    return {
        "apartment_number": apartment_number,
        "location": location,
        "apartment_type": apartment_type,
        "monthly_rent": monthly_rent,
        "num_rooms": num_rooms,
        "floor": floor,
        "size_sqft": size_sqft,
        "amenities": amenities,
        "status": "available",
        "current_tenant_id": None,
        "created_by": created_by,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
