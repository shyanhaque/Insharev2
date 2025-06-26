import time 

def get_quote_data(user_data):
    """Simulate quote data (replace with real SchemeServe later)"""
    return {
        "quote_id": f"SIM-{int(time.time())}",
        "premium": 85.00,
        "currency": "GBP",
        "valid_until": "2025-12-31",
        "details": f"{user_data['insurance_type'].capitalize()} Insurance Policy"
    }