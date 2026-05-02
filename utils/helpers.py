def parse_euro(value):
    if value is None:
        return 0
    return float(
        str(value)
        .replace("€", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )
