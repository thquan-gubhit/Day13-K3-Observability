from __future__ import annotations

import hashlib
import re

PII_PATTERNS: dict[str, str] = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "phone_vn": r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)",
    "cccd": r"\b\d{12}\b",
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    # Hộ chiếu VN: 1 chữ cái in hoa + 7-8 chữ số (ví dụ C1234567, P12345678).
    "passport": r"\b[A-Z]\d{7,8}\b",
    # Địa chỉ VN: che cả cụm "số nhà/đường/phường/... <phần còn lại của cụm>"
    # thay vì chỉ che từ khóa, vì phần định danh thật nằm ngay sau từ khóa.
    # Có cả biến thể không dấu vì người dùng thường gõ "so nha 12 duong Lang".
    # Cố ý KHÔNG thêm biến thể không dấu của "tổ/ấp/xã/ngõ": không dấu chúng
    # trùng với từ tiếng Anh thông dụng (to, ap, xa...) và sẽ xoá nhầm log.
    "address_vn": (
        r"(?i)\b(?:"
        r"số nhà|đường|ngõ|ngách|tổ|thôn|ấp|phường|xã|thị trấn|"
        r"quận|huyện|thị xã|tỉnh|thành phố"
        r"|so nha|duong|ngach|thon|phuong|thi tran|quan|huyen|thi xa|tinh|thanh pho"
        r")\b[^,.;\n]*"
    ),
}


def scrub_text(text: str) -> str:
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
