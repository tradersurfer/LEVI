from dataclasses import dataclass
from enum import Enum

class OrderSide(str, Enum):
    CALL="call"; PUT="put"; STOCK="stock"
class OrderType(str, Enum):
    LIMIT="limit"

@dataclass(frozen=True)
class BrokerOrder:
    symbol: str
    quantity: int
    side: OrderSide
    limit_price: float
    time_in_force: str = "DAY"
    order_type: OrderType = OrderType.LIMIT
    idempotency_key: str = ""
