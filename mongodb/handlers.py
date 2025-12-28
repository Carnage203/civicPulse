from mongodb.mongo_client import complaints_collection
from datetime import datetime
from bson import ObjectId
from typing import List


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

    for field, field_type in required_fields.items():
        if field not in complaint_data:
            raise ValueError(f"Missing required field: {field}")
        if not isinstance(complaint_data[field], field_type):
            raise TypeError(f"Invalid type for {field}. Expected {field_type}")

    complaint_data["created_at"] = datetime.utcnow()
    complaint_data["updated_at"] = datetime.utcnow()

    result = complaints_collection.insert_one(complaint_data)
    return str(result.inserted_id)

def get_complaint(complaint_id: str) -> dict:
    try:
        return complaints_collection.find_one({"_id": ObjectId(complaint_id)}) or {}
    except Exception as e:
        print(f"Error fetching complaint: {e}")
        return {}

def get_all_complaints(query: dict = None) -> list:
    try:
        return list(complaints_collection.find(query or {}))
    except Exception as e:
        print(f"Error fetching complaints: {e}")
        return []

def update_complaint(complaint_id: str, update_data: dict) -> bool:
    """
    Updates existing complaint details like status or category.
    No re-generation of summary since all summaries are pre-stored.
    """
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

def delete_complaint(complaint_id: str) -> bool:
    try:
        result = complaints_collection.delete_one({"_id": ObjectId(complaint_id)})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting complaint: {e}")
        return False

def get_complaints_by_status(status: str) -> list:
    try:
        return list(complaints_collection.find({"status": status}))
    except Exception as e:
        print(f"Error fetching complaints by status: {e}")
        return []


def update_complaint_status(complaint_id: str, new_status: str, extra_fields: dict = None) -> bool:
    """
    Updates complaint status and timestamps.
    Supports optional extra_fields (e.g., resolved_at).
    """
    try:
        update_fields = {
            "status": new_status,
            "updated_at": datetime.utcnow()
        }

        if extra_fields:
            update_fields.update(extra_fields)

        if new_status == "closed" and "resolved_at" not in update_fields:
            update_fields["resolved_at"] = datetime.utcnow()

        result = complaints_collection.update_one(
            {"_id": ObjectId(complaint_id)},
            {"$set": update_fields}
        )

        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating complaint status: {e}")
        return False
