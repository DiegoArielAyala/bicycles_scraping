def clean_price(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None    
    