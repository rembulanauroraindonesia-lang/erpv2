from datetime import datetime
from decimal import Decimal


def format_rupiah(value) -> str:
    if value is None:
        return "Rp 0"
    return "Rp {:,.0f}".format(Decimal(str(value))).replace(",", ".")


def format_date_wib(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
        return f"{value.day} {months[value.month - 1]} {value.year}"
    return str(value)
