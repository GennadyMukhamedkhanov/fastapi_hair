import re


def tone_sort_key(tone: str) -> tuple:
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
