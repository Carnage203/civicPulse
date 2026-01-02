from mongodb.handlers import get_all_complaints
from collections import Counter
from datetime import datetime

def get_analytics_data():
    list_complaints = get_all_complaints()
    totals = len(list_complaints)
    all_statuses = [complaint['status'] for complaint in list_complaints]
    category_counts = dict(Counter(
        complaint['category'] for complaint in list_complaints
    ))
    severity_counts = dict(Counter(
        complaint['severity_level'] for complaint in list_complaints
    ))
    block_complain_counts = dict(Counter(
        complaint['block'] for complaint in list_complaints
    ))
    
    open_sts = all_statuses.count('open')
    closed_sts = all_statuses.count('closed')
    junk_sts = all_statuses.count('junk')

    total_resolution_seconds = 0
    resolved_count = 0
    for complaint in list_complaints:
        created_at = complaint.get("created_at")
        resolved_at = complaint.get("resolved_at")

        if not created_at or not resolved_at:
            continue
        
        if isinstance(created_at, str):
            created_dt = datetime.fromisoformat(created_at)
        else:
            created_dt = created_at  

        if isinstance(resolved_at, str):
            resolved_dt = datetime.fromisoformat(resolved_at)
        else:
            resolved_dt = resolved_at  

        total_resolution_seconds += (resolved_dt - created_dt).total_seconds()
        resolved_count += 1

    avg_resolution_time = None
    if resolved_count > 0:
        avg_resolution_time = {
            "hours": round((total_resolution_seconds / resolved_count) / 3600, 2),
            "days": round((total_resolution_seconds / resolved_count) / 86400, 2)
        }
    
    return {
        "total_complaints": totals,
        "open_complaints": open_sts,
        "resolved_complaints": closed_sts,
        "junk_complaints": junk_sts,
        "category_counts": category_counts,
        "severity_counts": severity_counts,
        "block_counts": block_complain_counts,
        "average_resolution_time": avg_resolution_time
    }