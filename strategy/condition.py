"""Module for all the different conditions checker."""
from jsonpath_ng.ext import parse

def have_data(condition, data, **_kwargs):
    """Check if have data condition is true/false."""
    jsonpath_expr = condition.get("json_path")
    if not jsonpath_expr:
        return bool(data)

    jsonpath_expr = parse(jsonpath_expr)
    try:
        extracted_val = jsonpath_expr.find(data)[0].value
    except Exception:
        return False
    return bool(extracted_val)

def none(condition, data, **_kwargs):
    """Always return true."""
    return True

def no_data(condition, data, **_kwargs):
    """Check if scraped data still has value."""
    jsonpath_expr = condition.get("json_path")

    if not jsonpath_expr:
        return not bool(data)

    jsonpath_expr = parse(jsonpath_expr)
    try:
        extracted_val = jsonpath_expr.find(data)[0].value
    except Exception:
        return True
    return not bool(extracted_val)

def status_code(condition, data, gather_event=None):
    """Check if scraped data still has value."""
    status_code = condition.get("value")
    if gather_event["response_status_code"] == status_code:
        return True
    else:
        return False
