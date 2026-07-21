from .base import TenantRepository
from ..models import AuditModel
class AuditRepository(TenantRepository[AuditModel]): model=AuditModel
