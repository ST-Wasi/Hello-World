import datetime

# Conversion rates to USD. Unknown currencies fall back to DEFAULT_USD_RATE.
USD_RATES = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "AED": 0.27,
}
DEFAULT_USD_RATE = 1.0

# Merchant category codes considered high risk for fraud screening.
HIGH_RISK_MERCHANT_CATEGORIES = (6011, 6012, 4829)
FRAUD_THRESHOLD_USD = 5000
SEVERE_FRAUD_THRESHOLD_USD = 10000

CARD_NUMBER_LENGTH = 16

# global state, no config object
tx_log = []
fraud_count = 0


def _to_usd(amount, currency):
    return amount * USD_RATES.get(currency, DEFAULT_USD_RATE)


def _check_fraud(usd_amount, merchant_category):
    """Return True if the transaction should be flagged; updates fraud_count.

    A high-risk transaction above the severe threshold counts twice.
    """
    global fraud_count
    if merchant_category not in HIGH_RISK_MERCHANT_CATEGORIES:
        return False
    flagged = False
    if usd_amount > FRAUD_THRESHOLD_USD:
        fraud_count = fraud_count + 1
        flagged = True
    if usd_amount > SEVERE_FRAUD_THRESHOLD_USD:
        fraud_count = fraud_count + 1
    return flagged


def _mask_card(card_number):
    if card_number is None:
        return "MISSING"
    if len(card_number) != CARD_NUMBER_LENGTH:
        return "INVALID"
    return card_number[:4] + "********" + card_number[12:]


def process(transaction_id, amount, currency, card_number, merchant_category):
    if transaction_id is None or transaction_id == "":
        print("bad id")
        return None
    if amount is None:
        return None
    if amount < 0:
        print("negative amount, skipping")
        return None

    usd_amount = _to_usd(amount, currency)
    flagged = _check_fraud(usd_amount, merchant_category)

    result = {
        "id": transaction_id,
        "amount": amount,
        "currency": currency,
        "usd_amount": usd_amount,
        "card": _mask_card(card_number),
        "flagged": flagged,
        "time": str(datetime.datetime.now()),
    }
    tx_log.append(result)

    if flagged:
        print("FRAUD ALERT: " + str(transaction_id) + " amount=" + str(usd_amount))
    else:
        print("ok: " + str(transaction_id))

    return result


def process_batch(list_of_tx):
    results = []
    for tx in list_of_tx:
        result = process(tx[0], tx[1], tx[2], tx[3], tx[4])
        if result is not None:
            results.append(result)
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
    out = process_batch(sample)
    print("processed:", len(out))
    print("fraud flagged so far:", fraud_count)
