from datetime import datetime,timedelta,timezone
import requests
from levi.brokers.tastytrade.auth import TastytradeAuth
class R:
 def __init__(self,d,ok=True):self.d=d;self.ok=ok
 def raise_for_status(self):
  if not self.ok:raise requests.HTTPError()
 def json(self):return {"data":self.d}
class S:
 def __init__(self,r):self.r=r
 def post(self,*a,**k):return self.r
def test_auth_success():a=TastytradeAuth(S(R({"session-token":"a","remember-token":"r"})),"https://cert");assert a.authenticate("u","p") and a.access_token=="a"
def test_auth_failure():assert not TastytradeAuth(S(R({},False)),"https://cert").authenticate("u","p")
def test_expired():a=TastytradeAuth();assert a.is_token_expired()
def test_refresh():a=TastytradeAuth(S(R({"session-token":"b"})),"https://cert");a.refresh_token="r";assert a.refresh_access_token()
def test_header_refresh():a=TastytradeAuth(S(R({"session-token":"b"})),"https://cert");a.refresh_token="r";assert a.get_auth_header()["Authorization"]=="Bearer b"
