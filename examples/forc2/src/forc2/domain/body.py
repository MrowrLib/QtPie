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
