"""Order checkout.

The rules live in `src/shop/specs/checkout.md` - read it first.
Both functions below are stubs: their signature is final, the bodies are yours.
Do not change the constants: the tests rely on them.
"""

PROMO_CODES = {"WELCOME10": 10, "SUMMER15": 15, "VIP35": 35}
SUPPORTED_CITIES = ("msk", "spb")
MAX_DISCOUNT_PERCENT = 30
VAT_PERCENT = 20
SHIPPING_KOPEKS = 49_000
FREE_DELIVERY_FROM_KOPEKS = 500_000
TIER_DISCOUNTS = ((10, 5), (25, 10), (50, 15))
REQUIRED_LINE_KEYS = ("sku", "qty", "unit_price_kopecks")


def _validate_line(line: dict[str, str], seen_skus: set[str]) -> str | None:
    for key in REQUIRED_LINE_KEYS:
        if key not in line:
            return f"Missing key: {key}"

    sku = line["sku"]
    if not sku:
        return "Empty SKU"
    if sku in seen_skus:
        return f"Duplicate SKU: {sku}"
    seen_skus.add(sku)

    try:
        qty = int(line["qty"])
        price = int(line["unit_price_kopecks"])
    except ValueError:
        return "Non-numeric quantity or price"

    if qty <= 0:
        return "Quantity must be positive"
    if price < 0:
        return "Negative price"

    return None


def validate_order(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> str | None:
    """Return a human readable reason why the order is invalid, or None if it is fine."""
    if not lines:
        return "Order is empty"

    if shipping_city and shipping_city not in SUPPORTED_CITIES:
        return f"Unsupported city: {shipping_city}"

    if promo_code and promo_code not in PROMO_CODES:
        return f"Unknown promo code: {promo_code}"

    seen_skus: set[str] = set()
    for line in lines:
        err = _validate_line(line, seen_skus)
        if err:
            return err

    return None


def calculate_order_total(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> int | None:
    """Return the order total in kopecks, or None if the order is invalid."""
    if validate_order(lines, promo_code, shipping_city) is not None:
        return None

    subtotal = sum(int(line["qty"]) * int(line["unit_price_kopecks"]) for line in lines)

    # Расчет скидки
    total_qty = sum(int(line["qty"]) for line in lines)
    tier_discount = 0
    for min_qty, discount in sorted(TIER_DISCOUNTS, reverse=True):
        if total_qty >= min_qty:
            tier_discount = discount
            break

    promo_discount = PROMO_CODES.get(promo_code, 0)
    total_discount_percent = min(tier_discount + promo_discount, MAX_DISCOUNT_PERCENT)

    # Стоимость товара со скидкой
    discounted_subtotal = int(subtotal * (100 - total_discount_percent) / 100)

    # НДС 20%
    vat = int(discounted_subtotal * VAT_PERCENT / 100)
    total_goods = discounted_subtotal + vat

    # Доставка
    shipping = 0
    if shipping_city and subtotal < FREE_DELIVERY_FROM_KOPEKS:
        shipping = SHIPPING_KOPEKS

    return total_goods + shipping
