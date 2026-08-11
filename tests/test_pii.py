from app.logging_config import scrub_event
from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_compliance_identifiers_and_address() -> None:
    samples = {
        "cccd": ("CCCD 001201012345", "REDACTED_CCCD"),
        "credit_card": ("Card 4111 1111 1111 1111", "REDACTED_CREDIT_CARD"),
        "passport": ("Passport B1234567", "REDACTED_PASSPORT_VN"),
        "address": (
            "Địa chỉ: 123 Nguyễn Trãi, Phường 2, Quận 5",
            "REDACTED_ADDRESS_VN",
        ),
    }

    for raw, marker in samples.values():
        out = scrub_text(raw)
        assert raw not in out
        assert marker in out


def test_scrub_event_recursively_scrubs_all_string_values() -> None:
    event = {
        "event": "Contact student@vinuni.edu.vn",
        "top_level": "0901234567",
        "payload": {
            "nested": [
                "001201012345",
                {"card": "4111-1111-1111-1111"},
            ]
        },
    }

    scrubbed = scrub_event(None, "info", event)
    rendered = str(scrubbed)

    for secret in (
        "student@vinuni.edu.vn",
        "0901234567",
        "001201012345",
        "4111-1111-1111-1111",
    ):
        assert secret not in rendered
