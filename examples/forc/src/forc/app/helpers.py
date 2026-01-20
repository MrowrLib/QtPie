def filename_safe_validator(value: str) -> bool:
    """Validator for safe, clean filenames.

    NOTE: This is used as an input validator (character filter), so it validates
    individual characters as they're typed. Don't add empty/whitespace checks here -
    use widget-level validation (add_validator) for "must not be empty" rules.
    """
    # Only allow: letters, numbers, spaces, hyphens, underscores
    # No: /\?%*:|"<>()[]{}!@#$^&+=`~;',. etc
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_")
    return all(char in allowed for char in value)
