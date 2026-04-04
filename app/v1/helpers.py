from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

MONEY_Q = Decimal("0.01")
HUNDRED = Decimal("100")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_Q, rounding=ROUND_HALF_UP)


def calc_total_price(grams: int, price_per_100g: Decimal) -> Decimal:
    return money((Decimal(grams) * price_per_100g) / HUNDRED)


def calc_tax_amount(amount: Decimal, tax_rate: float) -> Decimal:
    return money(amount * Decimal(str(tax_rate)))


def calc_profit(
        grams: int,
        sale_price_per_100g: Decimal,
        purchase_price_per_100g: Decimal,
        tax_rate: float,
) -> Decimal:
    sale_total = calc_total_price(grams, sale_price_per_100g)
    purchase_total = calc_total_price(grams, purchase_price_per_100g)
    tax_amount = calc_tax_amount(sale_total, tax_rate)
    return money(sale_total - purchase_total - tax_amount)
