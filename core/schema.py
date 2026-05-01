from dataclasses import dataclass
from typing import List

@dataclass
class Order:
    numero_ordine: str
    data_ordine: str
    marketplace: str
    mercato: str
    fatturato_totale: float

@dataclass
class OrderRow:
    ordine_id: str
    sku_prodotto: str
    quantita: int
    prezzo_unitario: float
    totale_riga: float
