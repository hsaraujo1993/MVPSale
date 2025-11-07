from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def _quantize_money(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def apply_rounding(value: Decimal, strategy: str | None) -> Decimal:
    """Apply a rounding strategy to a monetary value.

    Supported strategies:
    - none (default): round to 2 decimals (HALF_UP)
    - psychological: round to X.99 (keeps integer part, cents = 0.99) when value >= 1
    - step:<size>: round up to the next multiple of <size> (e.g., step:0.10, step:0.05)
    """
    if value is None:
        return value
    if not strategy:
        return _quantize_money(value)

    s = (strategy or "none").strip().lower()
    if s == "none":
        return _quantize_money(value)

    if s == "psychological":
        # floor to integer, add 0.99; if less than 1.00, keep two decimals
        if value < Decimal("1"):
            return _quantize_money(value)
        integer_part = int(value)
        return Decimal(integer_part) + Decimal("0.99")

    if s.startswith("step:"):
        try:
            step_str = s.split(":", 1)[1]
            step = Decimal(step_str)
            if step <= 0:
                return _quantize_money(value)
            # ceil to next multiple of step
            multiples = (value / step).to_integral_value(rounding=ROUND_HALF_UP)
            # If exactly on multiple, keep; else bump if value > multiples*step
            candidate = step * multiples
            if candidate < value:
                candidate += step
            # align to step precision
            exp = Decimal(str(step)).as_tuple().exponent
            quant = Decimal(1).scaleb(exp)
            return candidate.quantize(quant, rounding=ROUND_HALF_UP)
        except Exception:
            return _quantize_money(value)

    return _quantize_money(value)

