from decimal import Decimal


def calc_row_total_beli(quantity, berat_beli_per_unit, hpp_per_unit):
    """Calculate row purchase total. If berat_beli > 0, use weight-based calc."""
    if berat_beli_per_unit and berat_beli_per_unit > 0:
        return quantity * berat_beli_per_unit * hpp_per_unit
    return quantity * hpp_per_unit


def calc_row_total_jual(quantity, berat_beli_per_unit, harga_jual_per_unit,
                         different_scale=False, berat_jual_per_unit=None):
    """Calculate row sales total. If different_scale, use berat_jual instead of berat_beli."""
    berat_jual = berat_jual_per_unit if (different_scale and berat_jual_per_unit) else berat_beli_per_unit
    if berat_jual and berat_jual > 0:
        return quantity * berat_jual * harga_jual_per_unit
    return quantity * harga_jual_per_unit


def calc_ppn(total_jual, price_mode):
    """Calculate PPN (11%). include_ppn = price already includes PPN. exclude_ppn = PPN added on top."""
    if price_mode == "include_ppn":
        ppn = (total_jual / Decimal("1.11")) * Decimal("0.11")
        grand_total = total_jual
    else:
        ppn = total_jual * Decimal("0.11")
        grand_total = total_jual + ppn
    return ppn, grand_total


def validate_penawaran_calc(items_data, price_mode):
    """Recalculate all totals server-side for validation."""
    total_beli = Decimal("0")
    total_jual = Decimal("0")

    for item in items_data:
        qty = Decimal(str(item["quantity"]))
        berat_beli = Decimal(str(item.get("berat_beli_per_unit", 0)))
        hpp = Decimal(str(item["hpp_per_unit"]))
        harga_jual = Decimal(str(item["harga_jual_per_unit"]))
        diff_scale = item.get("different_scale", False)
        berat_jual = Decimal(str(item.get("berat_jual_per_unit") or 0))

        row_beli = calc_row_total_beli(qty, berat_beli, hpp)
        row_jual = calc_row_total_jual(qty, berat_beli, harga_jual, diff_scale, berat_jual)

        total_beli += row_beli
        total_jual += row_jual

    ppn_amount, grand_total = calc_ppn(total_jual, price_mode)

    return {
        "total_beli": total_beli,
        "total_jual": total_jual,
        "ppn_amount": ppn_amount,
        "grand_total": grand_total,
    }
