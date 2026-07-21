import time
from levi.brokers.simulator import SimulatorBroker
from levi.execution.reconciler import ContinuousReconciler
from tests.broker_helpers import order
def test_start_stop():r=ContinuousReconciler(SimulatorBroker(),.01);r.start();r.stop();assert not r._running
def test_register():r=ContinuousReconciler(SimulatorBroker());r.on_fill("x",lambda *_:None);assert len(r._callbacks)==1
def test_callback():
 b=SimulatorBroker(1);o=b.submit_order(order());seen=[];r=ContinuousReconciler(b,.01);r.on_fill(o.order_id,lambda oid,f:seen.append(oid));r.start();time.sleep(.04);r.stop();assert seen==[o.order_id]
def test_callback_once():
 b=SimulatorBroker(1);o=b.submit_order(order());seen=[];r=ContinuousReconciler(b,.005);r.on_fill(o.order_id,lambda *_:seen.append(1));r.start();time.sleep(.03);r.stop();assert len(seen)==1
