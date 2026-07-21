from sqlalchemy.orm import Session
from ..models import UserModel

class UserRepository:
    def __init__(self, session: Session): self.session=session
    def upsert(self, user_id: str, email: str | None, provider: str) -> UserModel:
        user=self.session.get(UserModel,user_id)
        if user is None: user=UserModel(id=user_id,email=email,provider=provider); self.session.add(user)
        else: user.email,user.provider=email,provider
        self.session.flush(); return user
    def get(self, user_id: str) -> UserModel | None: return self.session.get(UserModel,user_id)
