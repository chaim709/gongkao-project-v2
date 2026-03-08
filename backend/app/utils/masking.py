"""敏感数据脱敏工具"""


def mask_phone(phone: str | None) -> str:
    """手机号脱敏：138****8000"""
    if not phone or len(phone) < 7:
        return phone or ""
    return phone[:3] + "****" + phone[-4:]


def mask_id_number(id_number: str | None) -> str:
    """身份证号脱敏：3201****0012"""
    if not id_number or len(id_number) < 8:
        return id_number or ""
    return id_number[:4] + "****" + id_number[-4:]


def mask_name(name: str | None) -> str:
    """姓名脱敏：张*"""
    if not name:
        return ""
    if len(name) <= 1:
        return name
    return name[0] + "*" * (len(name) - 1)
