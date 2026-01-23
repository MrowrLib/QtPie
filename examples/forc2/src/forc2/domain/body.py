"""Body - body type enum for HTTP requests."""

from enum import Enum


class BodyType(Enum):
    """Body types supported by Forc."""

    NONE = "none"
    JSON = "json"
    XML = "xml"
    TEXT = "text"
    FORM_URLENCODED = "form_urlencoded"
    FORM_DATA = "form_data"


BODY_TYPE_LABELS: dict[BodyType, str] = {
    BodyType.NONE: "No Body",
    BodyType.JSON: "JSON",
    BodyType.XML: "XML",
    BodyType.TEXT: "Plain Text",
    BodyType.FORM_URLENCODED: "Form URL Encoded",
    BodyType.FORM_DATA: "Form Data (multipart/form-data)",
}
