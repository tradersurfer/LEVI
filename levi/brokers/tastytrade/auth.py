import os
from datetime import datetime, timedelta, timezone
import requests

class TastytradeAuth:
    """OAuth/session-token manager. Credentials and tokens remain in memory."""
    def __init__(self, session=None, base_url=None):
        self.session=session or requests.Session(); self.base_url=(base_url or os.getenv("TASTYTRADE_API_URL","https://api.cert.tastyworks.com")).rstrip("/")
        self.access_token=None; self.refresh_token=None; self.expires_at=None; self.account_id=None
    def authenticate(self, username, password):
        try:
            r=self.session.post(f"{self.base_url}/sessions",json={"login":username,"password":password,"remember-me":True},timeout=10); r.raise_for_status(); d=r.json().get("data",r.json())
            self.access_token=d.get("session-token") or d.get("access_token"); self.refresh_token=d.get("remember-token") or d.get("refresh_token"); self.account_id=d.get("account-number")
            self.expires_at=datetime.now(timezone.utc)+timedelta(seconds=int(d.get("expires_in",3600))); return bool(self.access_token)
        except (requests.RequestException, ValueError, TypeError): return False
    def is_token_expired(self): return not self.expires_at or datetime.now(timezone.utc)>=self.expires_at
    def refresh_access_token(self):
        if not self.refresh_token:return False
        try:
            r=self.session.post(f"{self.base_url}/sessions",json={"remember-token":self.refresh_token},timeout=10); r.raise_for_status(); d=r.json().get("data",r.json()); self.access_token=d.get("session-token") or d.get("access_token"); self.expires_at=datetime.now(timezone.utc)+timedelta(seconds=int(d.get("expires_in",3600))); return bool(self.access_token)
        except (requests.RequestException, ValueError, TypeError): return False
    def get_auth_header(self):
        if self.is_token_expired() and not self.refresh_access_token(): raise RuntimeError("broker authentication expired")
        return {"Authorization":f"Bearer {self.access_token}"}

TastytradAuth=TastytradeAuth
