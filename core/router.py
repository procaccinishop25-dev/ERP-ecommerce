from core.temu_parser import parse_temu
from core.amazon_parser import parse_amazon

def parse_file(file, marketplace):

    if marketplace == "temu":
        return parse_temu(file)

    if marketplace == "amazon":
        return parse_amazon(file)

    raise Exception("Marketplace non supportato")
