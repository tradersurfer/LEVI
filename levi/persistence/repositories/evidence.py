from .base import TenantRepository
from ..models import EvidenceModel
class EvidenceRepository(TenantRepository[EvidenceModel]): model=EvidenceModel
