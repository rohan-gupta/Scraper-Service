"""Test the different conditions module."""
import ujson
import initiator.gather.variables as variables

def test_factory():
    """Test factory function."""
    key = "json_path"
    assert variables.variables_factory(key) == variables.json_path

def test_json_path():
    """Test json path extraction method."""
    with open("tests/common_test_data/eatigo_response.json", "r") as test_f:
        data = ujson.load(test_f)
    message = {
        "json_path": "$.id"
    }
    variable = variables.json_path(data["result"]["result"][0], message, "")
    assert variable == "1"

def test_set_value():
    """Test set value method."""
    message = {
        "value": 1
    }
    variable = variables.set_value("", message, "")
    assert variable == 1

    message["value"] = "2"
    variable = variables.set_value("", message, "")
    assert variable == "2"

def test_replace_value():
    """Test replace value method."""
    message = {
        "to_replace": "abc",
        "value": "def"
    }
    variable = variables.replace_value("abc", message, "")
    assert variable == "def"

    variable = variables.replace_value({"page": 1}, message, "")
    assert variable == {"page": 1}


def test_type_convert():
    """Test type convert method."""
    message = {
        "value": "str"
    }
    variable = variables.type_convert(2, message, "")
    assert variable == "2"

    message["value"] = "int"

    variable = variables.type_convert(2.0, message, "")
    assert variable == 2

def test_cookies():
    """Test cookies method."""
    cookies = {
        "location": "mock_location"
    }
    variable = variables.cookies(2, "", cookies)
    assert variable == cookies
