from .base import TenantRepository
from ..models import TradeModel
class TradeRepository(TenantRepository[TradeModel]): model=TradeModel
