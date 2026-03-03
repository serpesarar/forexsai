def safe_get_data(result):
    if not result:
        return []
    if isinstance(result, dict):
        return result.get("data") or []
    return getattr(result, "data", [])

def safe_get_error(result):
    if not result:
        return None
    if isinstance(result, dict):
        return result.get("error")
    return getattr(result, "error", None)
