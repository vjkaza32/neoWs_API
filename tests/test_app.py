import pytest as pytest
import pathlib
import logging
import pytest
import jsonschema

from api_connection_app import validate_json

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

root_folder = pathlib.Path(__file__).parent.resolve()

# Test Case 1: Valid JSON
def test_valid_json():
    jsonData = {
        "name": "James",
        "gender": "Male",
        "address": "467 Mayfield Ave",
        "age": 47
    }
    check_against_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "gender": {"type": "string"},
            "addgess": {"type": "string"},
            "age": {"type": "number"},
        },
        "required": ["name", "gender", "address", "age"]
    }

    # Expecting no exception to be raised
    assert validate_json(jsonData, check_against_schema) == True


# Test Case 2: Invalid JSON
def test_invalid_json():
    jsonData = {
        "name": "James",
        "gender": "Male",
        "address": "467 Mayfield Ave",
        "age": "47"
    }
    check_against_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "gender": {"type": "string"},
            "addgess": {"type": "string"},
            "age": {"type": "number"},
        },
        "required": ["name", "gender", "address", "age"]
    }

    # Expecting jsonschema.exceptions.ValidationError to be raised
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validate_json(jsonData, check_against_schema)


# Test Case 3: Missing Required Property
def test_missing_required_property():
    jsonData = {
        "name": "James",
        "gender": "Male",
        "address": "467 Mayfield Ave",
        "age": 47
    }
    check_against_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "gender": {"type": "string"},
            "addgess": {"type": "string"},
            "age": {"type": "number"},
            "occupation": {"type":"string"}
        },
        "required": ["name", "gender", "address", "age", "occupation"]
    }

    # Expecting jsonschema.exceptions.ValidationError to be raised
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validate_json(jsonData, check_against_schema)
