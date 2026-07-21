from .base import TenantRepository
from ..models import DecisionModel
class DecisionRepository(TenantRepository[DecisionModel]): model=DecisionModel
