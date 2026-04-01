import re

from app.common.models import HairProduct


def tone_sort_key(tone: str) -> tuple:
    """ Сортировка по тону. """

    # Числовой формат (1.0, 12.0, 6.35)
    if re.match(r'^\d+(\.\d+)?$', tone):
        return (1, float(tone))
    # Буквенно-цифровой (4TN, 9BG)
    elif re.match(r'^\d+[A-Z]+$', tone):
        numeric_part = int(re.match(r'^\d+', tone).group())
        return (2, numeric_part, tone)
    # Смешанный (OB 6/12)
    else:
        return (3, tone)


def tone_and_length_sort_key(product: HairProduct) -> tuple:
    """ Сортировка по тону и длине. """
    # 1. Сначала по тону
    tone = product.tone.tone  # "6.0", "6.35", "4TN"

    # Числовой формат (1.0, 12.0, 6.35)
    if re.match(r'^\d+(\.\d+)?$', tone):
        tone_key = (1, float(tone))
    # Буквенно-цифровой (4TN, 9BG)
    elif re.match(r'^\d+[A-Z]+$', tone):
        numeric_part = int(re.match(r'^\d+', tone).group())
        tone_key = (2, numeric_part, tone)
    # Смешанный (OB 6/12)
    else:
        tone_key = (3, tone)

    # 2. Затем по длине
    return (*tone_key, product.length_cm)