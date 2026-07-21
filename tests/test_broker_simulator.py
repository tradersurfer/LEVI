from levi.brokers import OrderStatus
from levi.brokers.simulator import SimulatorBroker
from tests.broker_helpers import order
def test_simulator_auth(): b=SimulatorBroker();assert b.authenticate({}) and b.is_connected()
def test_simulator_receipt(): b=SimulatorBroker();assert b.submit_order(order()).status is OrderStatus.WORKING
def test_simulator_fills(): b=SimulatorBroker(1);r=b.submit_order(order());assert b.get_order_status(r.order_id) is OrderStatus.FILLED and b.get_fills(r.order_id)
def test_simulator_cancel(): b=SimulatorBroker();r=b.submit_order(order());assert b.cancel_order(r.order_id)
def test_simulator_open_orders(): b=SimulatorBroker();r=b.submit_order(order());assert b.get_open_orders()==[r]
def test_simulator_order_history(): b=SimulatorBroker();r=b.submit_order(order());b.cancel_order(r.order_id);assert len(b.get_order_history())==1
