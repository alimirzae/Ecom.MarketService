import re

PERSIAN_DIGITS = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹",
    "0123456789"
)

ARABIC_DIGITS = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩",
    "0123456789"
)


def normalize_number(value: str) -> int:
    """
    Converts Persian numbers to integer.

    Examples

    ۱۸۸,۷۰۰ -> 188700

    -۱,۲۰۰ -> -1200
    """

    if value is None:
        return 0

    value = value.translate(PERSIAN_DIGITS)
    value = value.translate(ARABIC_DIGITS)

    value = value.replace(",", "")

    value = value.replace("٬", "")

    value = value.strip()

    value = re.sub(r"[^\d\-]", "", value)

    if value == "":
        return 0

    return int(value)