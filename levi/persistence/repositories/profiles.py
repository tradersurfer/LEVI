from .base import TenantRepository
from ..models import ProfileModel
class ProfileRepository(TenantRepository[ProfileModel]): model=ProfileModel
