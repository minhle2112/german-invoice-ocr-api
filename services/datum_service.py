from datetime import datetime

def normalize_date(date_str):
    if not date_str:
        return None

    formats = [
        "%d.%m.%Y",
        "%d.%m.%y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except:
            continue

    return None