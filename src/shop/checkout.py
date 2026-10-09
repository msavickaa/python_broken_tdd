"""Order checkout.

The rules live in `src/shop/specs/checkout.md` - read it first.
Both functions below are stubs: their signature is final, the bodies are yours.
Do not change the constants: the tests rely on them.
"""

import re

from shop.money import percent_of

PROMO_CODES = {"WELCOME10": 10, "SUMMER15": 15, "VIP35": 35}
SUPPORTED_CITIES = ("msk", "spb")
MAX_DISCOUNT_PERCENT = 30
VAT_PERCENT = 20
SHIPPING_KOPEKS = 49_000
FREE_DELIVERY_FROM_KOPEKS = 500_000
TIER_DISCOUNTS = ((10, 5), (25, 10), (50, 15))
REQUIRED_LINE_KEYS = ("sku", "qty", "unit_price_kopecks")

_NUMBER = re.compile(r"[+-]?\d+")


def _parse_number(value: str) -> int | None:
    """Parse a numeric string without raising.

    Returns ``int`` when ``int()`` accepts the value
    (whitespace and an optional sign at the edges are fine),
    otherwise ``None``.
    """
    token = value.strip()
    if _NUMBER.fullmatch(token) is None:
        return None
    return int(value)


def _check_required_keys(line: dict[str, str], index: int) -> str | None:
    """Return a reason if one of ``REQUIRED_LINE_KEYS`` is absent from ``line``."""
    for key in REQUIRED_LINE_KEYS:
        if key not in line:
            return f"line {index} is missing key {key!r}"
    return None


def _validate_qty(line: dict[str, str], index: int) -> str | None:
    """Validate the ``qty`` field of one order line."""
    qty = _parse_number(line["qty"])
    if qty is None:
        return f"line {index} qty is not a number"
    if qty <= 0:
        return f"line {index} qty is not greater than zero"
    return None


def _validate_price(line: dict[str, str], index: int) -> str | None:
    """Validate the ``unit_price_kopecks`` field of one order line."""
    price = _parse_number(line["unit_price_kopecks"])
    if price is None:
        return f"line {index} unit_price_kopecks is not a number"
    if price < 0:
        return f"line {index} price is negative"
    return None


def _validate_one_line(line: dict[str, str], index: int) -> str | None:
    """Validate a single order line according to spec rules 2-7."""
    reason = _check_required_keys(line, index)
    if reason is not None:
        return reason

    if line["sku"] == "":
        return f"line {index} has empty sku"

    reason = _validate_qty(line, index)
    if reason is not None:
        return reason

    return _validate_price(line, index)


def _validate_lines(lines: list[dict[str, str]]) -> str | None:
    """Validate the order lines according to spec rules 1 and 8."""
    if not lines:
        return "order has no lines"

    seen_skus: set[str] = set()

    for index, line in enumerate(lines, start=1):
        # Validate the line first so that all ``REQUIRED_LINE_KEYS`` are present
        # before any key access below, and rules 3-7 take precedence over rule 8.
        reason = _validate_one_line(line, index)
        if reason is not None:
            return reason

        sku = line["sku"]
        if sku in seen_skus:
            return f"line {index} has duplicate sku {sku!r}"
        seen_skus.add(sku)

    return None


def _validate_promo_code(promo_code: str) -> str | None:
    """Rule 9: reject an unknown promo code."""
    if promo_code != "" and promo_code not in PROMO_CODES:
        return f"unknown promo code {promo_code!r}"
    return None


def _validate_shipping_city(shipping_city: str) -> str | None:
    """Rule 10: reject an unsupported shipping city."""
    if shipping_city != "" and shipping_city not in SUPPORTED_CITIES:
        return f"city {shipping_city!r} is not supported"
    return None


def validate_order(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> str | None:
    """Return a human readable reason why the order is invalid, or None if it is fine."""
    reason = _validate_lines(lines)
    if reason is not None:
        return reason

    reason = _validate_promo_code(promo_code)
    if reason is not None:
        return reason

    return _validate_shipping_city(shipping_city)


def calculate_order_total(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> int | None:
    """Return the order total in kopecks, or None if the order is invalid."""
    reason = validate_order(lines, promo_code, shipping_city)
    if reason is not None:
        return None

    subtotal = 0
    total_qty = 0

    for line in lines:
        qty = int(line["qty"])
        unit_price = int(line["unit_price_kopecks"])
        subtotal += qty * unit_price
        total_qty += qty

    tier_percent = 0
    for threshold, percent in TIER_DISCOUNTS:
        if total_qty >= threshold:
            tier_percent = percent

    promo_percent = PROMO_CODES.get(promo_code, 0)
    discount_percent = max(tier_percent, promo_percent)

    if discount_percent > MAX_DISCOUNT_PERCENT:
        discount_percent = MAX_DISCOUNT_PERCENT

    discount = percent_of(subtotal, discount_percent)
    discounted_subtotal = subtotal - discount

    if shipping_city != "" and discounted_subtotal < FREE_DELIVERY_FROM_KOPEKS:
        delivery = SHIPPING_KOPEKS
    else:
        delivery = 0

    base = discounted_subtotal + delivery
    vat = percent_of(base, VAT_PERCENT)
    return base + vat
