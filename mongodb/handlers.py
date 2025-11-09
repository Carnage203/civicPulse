from mongodb.mongo_client import complaints_collection
from datetime import datetime
from bson import ObjectId
from typing import List
from llm.chat import embed_generator


# =====================================================
# ✅ Create a new complaint
# =====================================================
def create_complaint(complaint_data: dict) -> str:
    required_fields = {
        "resident_name": str,
        "block": str,
        "description": str,
        "category": str,
        "sentiment": str,
        "severity_level": str,
        "urgency_score": int,
        "llm_summary": str,
        "action_recommendation": str,
        "embedding": list,
        "status": str
    }

    # Validation
    for field, field_type in required_fields.items():
        if field not in complaint_data:
            raise ValueError(f"Missing required field: {field}")
        if not isinstance(complaint_data[field], field_type):
            raise TypeError(f"Invalid type for {field}. Expected {field_type}")

    # Add timestamps
    complaint_data["created_at"] = datetime.utcnow()
    complaint_data["updated_at"] = datetime.utcnow()

    result = complaints_collection.insert_one(complaint_data)
    return str(result.inserted_id)


# =====================================================
# ✅ Retrieve a single complaint
# =====================================================
def get_complaint(complaint_id: str) -> dict:
    try:
        return complaints_collection.find_one({"_id": ObjectId(complaint_id)}) or {}
    except Exception as e:
        print(f"Error fetching complaint: {e}")
        return {}


# =====================================================
# ✅ Retrieve all complaints
# =====================================================
def get_all_complaints(query: dict = None) -> list:
    try:
        return list(complaints_collection.find(query or {}))
    except Exception as e:
        print(f"Error fetching complaints: {e}")
        return []


# =====================================================
# ✅ Update complaint details
# =====================================================
def update_complaint(complaint_id: str, update_data: dict) -> bool:
    try:
        update_data["updated_at"] = datetime.utcnow()
        result = complaints_collection.update_one(
            {"_id": ObjectId(complaint_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating complaint: {e}")
        return False


# =====================================================
# ✅ Delete a complaint
# =====================================================
def delete_complaint(complaint_id: str) -> bool:
    try:
        result = complaints_collection.delete_one({"_id": ObjectId(complaint_id)})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting complaint: {e}")
        return False


# =====================================================
# ✅ Get complaints by status
# =====================================================
def get_complaints_by_status(status: str) -> list:
    try:
        return list(complaints_collection.find({"status": status}))
    except Exception as e:
        print(f"Error fetching complaints by status: {e}")
        return []


# =====================================================
# ✅ Update complaint status (Pending → Resolved/Junk)
# =====================================================
def update_complaint_status(complaint_id: str, new_status: str) -> bool:
    try:
        update_fields = {
            "status": new_status,
            "updated_at": datetime.utcnow()
        }

        # If resolved, add timestamp
        if new_status == "closed":
            update_fields["resolved_at"] = datetime.utcnow()

        result = complaints_collection.update_one(
            {"_id": ObjectId(complaint_id)},
            {"$set": update_fields}
        )

        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating complaint status: {e}")
        return False


# # ===============================
# # --- STATUS MANAGEMENT HELPERS ---
# # ===============================

# def get_complaints_by_status(status: str) -> list:
#     """Fetch all complaints filtered by status."""
#     try:
#         return list(complaints_collection.find({"status": status}))
#     except Exception as e:
#         print(f"Error fetching complaints by status: {e}")
#         return []


# def update_complaint_status(complaint_id: str, new_status: str) -> bool:
#     """Update the complaint status and optionally add resolved_at timestamp."""
#     try:
#         update_fields = {
#             "status": new_status,
#             "updated_at": datetime.utcnow()
#         }

#         if new_status == "closed":
#             update_fields["resolved_at"] = datetime.utcnow()

#         result = complaints_collection.update_one(
#             {"_id": ObjectId(complaint_id)},
#             {"$set": update_fields}
#         )

#         return result.modified_count > 0
#     except Exception as e:
#         print(f"Error updating complaint status: {e}")
#         return False

