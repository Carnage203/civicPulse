from agents import analyze_complaint

payload = {
    "resident_name": "Ritika Sharma",
    "block": "Sector 8",
    "description": "Street lights have not been working for the past 3 nights and the area feels unsafe."
}

result = analyze_complaint(payload)
print(result)
