from datetime import datetime,timezone
from levi.brokers.base import Fill,Position
from levi.brokers.models import BrokerOrder,OrderSide
def order(**kw):
 d=dict(symbol="SPY  260821C00500000",quantity=1,side=OrderSide.CALL,limit_price=2.5,idempotency_key="k");d.update(kw);return BrokerOrder(**d)
def fill(oid="1",price=2.5,qty=1):return Fill(oid,"SPY",qty,price,datetime.now(timezone.utc),"call")
def pos(symbol="SPY",u=2,r=1):return Position(symbol,1,100,103,u,r)
