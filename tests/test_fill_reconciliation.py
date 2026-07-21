from levi.brokers import OrderStatus
from levi.brokers.tastytrade.reconciliation import FillReconciler
from tests.broker_helpers import fill
class C:
 def get_order_status(self,x):return OrderStatus.FILLED
 def get_order_fills(self,x):return [fill(x)]
def test_reconcile_order(): assert FillReconciler(C()).reconcile_order("1").average_fill_price==2.5
def test_missing_fill(): assert "Missing fill" in FillReconciler(C()).verify_integrity([], [fill()])
def test_price_deviation(): assert "Price deviation" in FillReconciler(C()).verify_integrity([fill(price=1)],[fill(price=2)])
def test_record_fill(): r=FillReconciler(C());r.record_fill("1",fill());assert r._recorded_fills["1"]
