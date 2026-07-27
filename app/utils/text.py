import codecs


def decode_js_string(value: str) -> str:
    """
    Decode JavaScript escaped unicode text.

    Example:
        \\u062f\\u0644\\u0627\\u0631
            ->
        دلار
    """

    if not value:
        return value

    if "\\u" in value or "\\x" in value:
        return codecs.decode(value, "unicode_escape")

    return value