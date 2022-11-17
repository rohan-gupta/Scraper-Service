"""Module to create variables based on different methods."""
from jsonpath_ng.ext import parse

def variables_factory(key):
    """Function to return which variable method to use."""
    methods = {
        "json_path": json_path,
        "set_value": set_value,
        "replace_value": replace_value,
        "type_convert": type_convert,
        "cookies": cookies
    }
    return methods[key]

def json_path(data, message, _cookies):
    """Extract value based on json path."""
    jsonpath_expr = message["json_path"]

    jsonpath_expr = parse(jsonpath_expr)
    try:
        extracted_val = jsonpath_expr.find(data)
        if len(extracted_val) > 1:
            extracted_val = [datum.value for datum in extracted_val]
        else:
            extracted_val = extracted_val[0].value
    except Exception:
        extracted_val = None
    return extracted_val

def set_value(_data, message, _cookies):
    """Set fixed value."""
    return message["value"]

def replace_value(data, message, _cookies):
    """Set fixed value."""
    try:
        extracted = data.replace(message["to_replace"], message["value"])
    except Exception as e:
        extracted = data
        print(e)
    return extracted

def type_convert(data, message, _cookies):
    """Convert variable type."""
    data_type = message["value"]
    if data_type == "int":
        extracted = int(data)
    elif data_type == "str":
        extracted = str(data)
    elif data_type == "list":
        if not isinstance(data, list):
            extracted = [data]
        else:
            extracted = data
    return extracted

def cookies(data, message, cookies):
    """Convert variable type."""
    return cookies
