import os
from datetime import datetime, timezone
import requests
from ..base import Account, Fill, OrderReceipt, OrderStatus, Position
from ..models import OrderType
from .auth import TastytradeAuth

def _data(r): r.raise_for_status(); return r.json().get("data",r.json())
def _status(v):
    v=str(v).lower().replace(" ","_"); aliases={"received":OrderStatus.WORKING,"live":OrderStatus.WORKING,"cancelled":OrderStatus.CANCELED,"partially_filled":OrderStatus.PARTIAL}; return aliases[v] if v in aliases else OrderStatus(v)
def _receipt(x):
    legs=x.get("legs") or [{}]; leg=legs[0]
    timestamp=x.get("received-at") or x.get("updated-at")
    parsed=datetime.fromisoformat(str(timestamp).replace("Z","+00:00")) if timestamp else datetime.now(timezone.utc)
    return OrderReceipt(str(x.get("id")),_status(x.get("status","working")),str(leg.get("symbol",x.get("symbol",""))),int(float(leg.get("quantity",x.get("quantity",0)))),float(x.get("price",x.get("limit-price",0))),str(x.get("side",leg.get("action","call"))),parsed)
class TastytradeClient:
    """Paper-certificate endpoint client; refuses non-paper base URLs."""
    def __init__(self, username="", password="", session=None, base_url=None):
        self.session=session or requests.Session(); self.base_url=(base_url or os.getenv("TASTYTRADE_API_URL","https://api.cert.tastyworks.com")).rstrip("/")
        if "cert" not in self.base_url.lower() and "sandbox" not in self.base_url.lower(): raise ValueError("paper/sandbox Tastytrade API URL required")
        self.auth=TastytradeAuth(self.session,self.base_url); self.username=username; self.password=password; self.account_id=os.getenv("TASTYTRADE_PAPER_ACCOUNT_ID","")
    def authenticate(self, credentials=None):
        c=credentials or {}; ok=self.auth.authenticate(c.get("username",self.username),c.get("password",self.password)); self.account_id=self.account_id or self.auth.account_id or ""; return ok
    def _headers(self): return self.auth.get_auth_header()
    def get_account(self):
        d=_data(self.session.get(f"{self.base_url}/accounts/{self.account_id}/balances",headers=self._headers(),timeout=10)); return Account(self.account_id,float(d.get("net-liquidating-value",0)),float(d.get("derivative-buying-power",0)),datetime.now(timezone.utc))
    def get_positions(self):
        d=_data(self.session.get(f"{self.base_url}/accounts/{self.account_id}/positions",headers=self._headers(),timeout=10)); rows=d.get("items",d) if isinstance(d,dict) else d
        return [Position(str(x.get("symbol","")),int(float(x.get("quantity",0))),float(x.get("average-open-price",0)),float(x.get("close-price",0)),float(x.get("unrealized-day-gain",0)),float(x.get("realized-day-gain",0))) for x in rows]
    def submit_limit_order(self, order):
        if order.order_type is not OrderType.LIMIT: raise ValueError("only LIMIT orders allowed")
        if order.quantity<=0 or order.limit_price<=0 or not order.symbol.strip(): raise ValueError("invalid order")
        body={"time-in-force":order.time_in_force,"order-type":"Limit","price":str(order.limit_price),"legs":[{"instrument-type":"Equity Option","symbol":order.symbol,"quantity":order.quantity,"action":"Buy to Open"}]}
        d=_data(self.session.post(f"{self.base_url}/accounts/{self.account_id}/orders",json=body,headers=self._headers(),timeout=10)); return OrderReceipt(str(d.get("order",d).get("id")),_status(d.get("order",d).get("status","working")),order.symbol,order.quantity,order.limit_price,order.side.value,datetime.now(timezone.utc))
    submit_order=submit_limit_order
    def get_order_status(self, oid): return _status(_data(self.session.get(f"{self.base_url}/accounts/{self.account_id}/orders/{oid}",headers=self._headers(),timeout=10)).get("status","working"))
    def get_order_fills(self, oid):
        d=_data(self.session.get(f"{self.base_url}/accounts/{self.account_id}/orders/{oid}/fills",headers=self._headers(),timeout=10)); rows=d.get("items",d) if isinstance(d,dict) else d
        return [Fill(oid,str(x["symbol"]),int(x["quantity"]),float(x["price"]),datetime.fromisoformat(str(x["fill-time"]).replace("Z","+00:00")),str(x.get("side","call"))) for x in rows]
    get_fills=get_order_fills
    def _orders(self, path):
        d=_data(self.session.get(f"{self.base_url}/accounts/{self.account_id}/{path}",headers=self._headers(),timeout=10)); rows=d.get("items",d) if isinstance(d,dict) else d
        return [_receipt(x) for x in rows]
    def get_open_orders(self): return self._orders("orders/live")
    def get_order_history(self): return self._orders("orders")
    def cancel_order(self,oid): return self.session.delete(f"{self.base_url}/accounts/{self.account_id}/orders/{oid}",headers=self._headers(),timeout=10).status_code in (200,204)
    def is_connected(self):
        try:self.get_account(); return True
        except (requests.RequestException,RuntimeError,ValueError,KeyError):return False
