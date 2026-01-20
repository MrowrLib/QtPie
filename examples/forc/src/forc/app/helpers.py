from qtpie import confirm, is_dark_mode


def filename_safe_validator(value: str) -> bool:
    """Validator for safe, clean filenames.

    NOTE: This is used as an input validator (character filter), so it validates
    individual characters as they're typed. Don't add empty/whitespace checks here -
    use widget-level validation (add_validator) for "must not be empty" rules.
    """
    # Only allow: letters, numbers, spaces, hyphens, underscores
    # No: /\?%*:|"<>()[]{}!@#$^&+=`~;',. etc
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789() -_")
    return all(char in allowed for char in value)


def confirm_delete(
    message: str = "Are you sure you want to delete the selected item?", title: str = "Confirm Deletion"
) -> bool:
    """Show a confirmation dialog for deletions."""

    delete_icon = ":/trash-dark.svg" if is_dark_mode() else ":/trash-light.svg"
    return confirm(text=message, title=title, icon=delete_icon, buttons={"yes": "Delete", "no": "Cancel"})
