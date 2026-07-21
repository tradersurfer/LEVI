import pytest
from levi.brokers.tastytrade.client import TastytradeClient
class Response:
 def __init__(self,items):self.items=items
 def raise_for_status(self):pass
 def json(self):return {"data":{"items":self.items}}
class Session:
 def __init__(self,items):self.items=items;self.urls=[]
 def get(self,url,**kwargs):self.urls.append(url);return Response(self.items)
def client_with_orders():
 s=Session([{"id":"7","status":"Live","price":"2.50","received-at":"2026-07-21T12:00:00Z","legs":[{"symbol":"SPY OPT","quantity":2,"action":"Buy to Open"}]}]);c=TastytradeClient(session=s,base_url="https://api.cert.tastyworks.com");c.account_id="PAPER";c.auth.access_token="token";c.auth.expires_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc)+__import__("datetime").timedelta(hours=1);return c,s
def test_reject_live_url():
 with pytest.raises(ValueError):TastytradeClient(base_url="https://api.tastyworks.com")
def test_accept_cert_url():assert "cert" in TastytradeClient(base_url="https://api.cert.tastyworks.com").base_url
def test_get_open_orders_parses_receipts():
 c,s=client_with_orders();orders=c.get_open_orders();assert orders[0].order_id=="7" and orders[0].quantity==2 and s.urls[0].endswith("/orders/live")
def test_get_order_history_parses_receipts():
 c,s=client_with_orders();orders=c.get_order_history();assert orders[0].limit_price==2.5 and s.urls[0].endswith("/orders")
