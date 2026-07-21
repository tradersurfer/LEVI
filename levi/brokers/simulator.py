from datetime import datetime, timezone
from uuid import uuid4
from .base import Account, Fill, OrderReceipt, OrderStatus, Position

class SimulatorBroker:
    """Deterministic paper-only broker used for tests and development."""
    def __init__(self, fill_after_polls=2):
        self.connected=False; self.fill_after_polls=fill_after_polls; self.orders={}; self.polls={}; self.fills={}; self.positions={}
    def authenticate(self, credentials): self.connected=True; return True
    def is_connected(self): return self.connected
    def get_account(self): return Account("paper",100000,100000,datetime.now(timezone.utc))
    def get_positions(self): return list(self.positions.values())
    def submit_order(self, order):
        oid=str(uuid4()); r=OrderReceipt(oid,OrderStatus.WORKING,order.symbol,order.quantity,order.limit_price,order.side.value,datetime.now(timezone.utc)); self.orders[oid]=r; self.polls[oid]=0; return r
    submit_limit_order=submit_order
    def get_order_status(self, order_id):
        r=self.orders[order_id]
        if r.status in (OrderStatus.CANCELED,OrderStatus.FILLED): return r.status
        self.polls[order_id]+=1
        if self.polls[order_id]>=self.fill_after_polls:
            f=Fill(order_id,r.symbol,r.quantity,r.limit_price,datetime.now(timezone.utc),r.side); self.fills[order_id]=[f]
            self.orders[order_id]=OrderReceipt(**{**r.__dict__,"status":OrderStatus.FILLED})
        return self.orders[order_id].status
    def get_fills(self, order_id): return list(self.fills.get(order_id,[]))
    def get_open_orders(self): return [r for r in self.orders.values() if r.status in (OrderStatus.WORKING,OrderStatus.PARTIAL)]
    def get_order_history(self): return list(self.orders.values())
    def cancel_order(self, order_id):
        r=self.orders.get(order_id)
        if not r or r.status is not OrderStatus.WORKING:return False
        self.orders[order_id]=OrderReceipt(**{**r.__dict__,"status":OrderStatus.CANCELED}); return True
