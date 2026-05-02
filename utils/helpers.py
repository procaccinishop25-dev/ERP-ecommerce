def parse_euro(x):
    if not x:
        return 0
    return float(str(x).replace("€","").replace(",","."))
