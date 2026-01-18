def filename_safe_validator(value: str) -> bool:
    """Validator for safe, clean filenames."""
    if not value or not value.strip():
        return False
    # Only allow: letters, numbers, spaces, hyphens, underscores
    # No: /\?%*:|"<>()[]{}!@#$^&+=`~;',. etc
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_")
    return all(char in allowed for char in value)
