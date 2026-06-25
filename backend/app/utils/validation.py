

from marshmallow import ValidationError


def validate_request(schema, data):
    """
    Validates incoming data against a marshmallow schema.
    Returns (validated_data, None) on success, or (None, error_response) on failure.
    """
    try:
        return schema.load(data), None
    except ValidationError as err:
        return None, {"error": "Validation failed", "details": err.messages}