# test_agents.py

from agents import analyze_complaint

# Sample complaint payload
payload = {
    "resident_name": "Ritika Sharma",
    "block": "Sector 8",
    "description": "Street lights have not been working for the past 3 nights and the area feels unsafe."
}

# Call the function
result = analyze_complaint(payload)

# Print formatted output
import json
print(json.dumps(result, indent=4))
