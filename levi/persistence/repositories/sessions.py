from .base import TenantRepository
from ..models import SessionModel
class SessionRepository(TenantRepository[SessionModel]): model=SessionModel
