from dataclasses import dataclass
from . import client as _unused
from ..base import Fill, OrderStatus
@dataclass(frozen=True)
class ReconciliationResult:
    order_id:str;status:OrderStatus;fills:list[Fill];total_filled:int;average_fill_price:float;discrepancies:list[str]
class FillReconciler:
    def __init__(self,client,price_tolerance=.01):self.client=client;self.price_tolerance=price_tolerance;self._recorded_fills={}
    def record_fill(self,oid,fill):self._recorded_fills.setdefault(oid,[]).append(fill)
    def verify_integrity(self,recorded,broker):
        issues=[]
        if len(broker)>len(recorded):issues.append("Missing fill")
        if sum(x.quantity for x in recorded)!=sum(x.quantity for x in broker):issues.append("Quantity mismatch")
        for a,b in zip(recorded,broker):
            if abs(a.fill_price-b.fill_price)>self.price_tolerance:issues.append("Price deviation")
        return list(dict.fromkeys(issues))
    def reconcile_order(self,oid):
        status=self.client.get_order_status(oid); fills=self.client.get_order_fills(oid); qty=sum(x.quantity for x in fills); avg=sum(x.quantity*x.fill_price for x in fills)/qty if qty else 0.0
        return ReconciliationResult(oid,status,fills,qty,avg,self.verify_integrity(self._recorded_fills.get(oid,[]),fills))
