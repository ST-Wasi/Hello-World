import datetime
import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    # Conversion rates to USD. Currencies not listed here are rejected.
    usd_rates: dict = field(default_factory=lambda: {
        "USD": 1.0,
        "EUR": 1.08,
        "GBP": 1.27,
        "AED": 0.27,
    })
    card_number_length: int = 16


class ValidationError(ValueError):
    pass


def _validate(config, transaction_id, amount, currency, card_number, merchant_category):
    if not isinstance(transaction_id, str) or not transaction_id.strip():
        raise ValidationError("transaction_id must be a non-empty string")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValidationError("amount must be a number")
    if not math.isfinite(amount):
        raise ValidationError("amount must be finite")
    if amount < 0:
        raise ValidationError("amount must not be negative")
    if currency not in config.usd_rates:
        raise ValidationError("unsupported currency: " + repr(currency))
    if card_number is not None and not isinstance(card_number, str):
        raise ValidationError("card_number must be a string or None")
    if isinstance(merchant_category, bool) or not isinstance(merchant_category, int):
        raise ValidationError("merchant_category must be an integer")


class TransactionProcessor:
    def __init__(self, config=None):
        self.config = config or Config()
        self.tx_log = []

    def _to_usd(self, amount, currency):
        return amount * self.config.usd_rates[currency]

    def _mask_card(self, card_number):
        if card_number is None:
            return "MISSING"
        if len(card_number) != self.config.card_number_length or not card_number.isdigit():
            return "INVALID"
        return card_number[:4] + "*" * (len(card_number) - 8) + card_number[-4:]

    def process(self, transaction_id, amount, currency, card_number, merchant_category):
        """Validate and record a transaction. Raises ValidationError on bad input."""
        _validate(self.config, transaction_id, amount, currency, card_number, merchant_category)

        result = {
            "id": transaction_id,
            "amount": amount,
            "currency": currency,
            "usd_amount": self._to_usd(amount, currency),
            "card": self._mask_card(card_number),
            "merchant_category": merchant_category,
            "time": str(datetime.datetime.now()),
        }
        self.tx_log.append(result)
        print("ok: " + transaction_id)
        return result

    def process_batch(self, list_of_tx):
        """Process each transaction, skipping (and reporting) invalid ones."""
        results = []
        for tx in list_of_tx:
            try:
                if len(tx) != 5:
                    raise ValidationError("expected 5 fields, got " + str(len(tx)))
                results.append(self.process(*tx))
            except ValidationError as e:
                print("skipping " + repr(tx[0] if tx else None) + ": " + str(e))
        return results


# sample data to run it
if __name__ == "__main__":
    sample = [
        ("TX1001", 4500, "USD", "4111111111111111", 5411),
        ("TX1002", 12000, "EUR", "5500000000000004", 6011),
        ("TX1003", -50, "GBP", "340000000000009", 5812),
        ("TX1004", 200, "AED", None, 6012),
        ("TX1005", 9000, "USD", "4111111111111111", 4829),
    ]
    processor = TransactionProcessor(Config())
    out = processor.process_batch(sample)
    print("processed:", len(out))
