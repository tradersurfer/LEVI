import pytest
from levi.brokers.tastytrade.orders import OrderSubmitter
from levi.brokers.simulator import SimulatorBroker
from tests.broker_helpers import order
def test_submit_limit_order(): assert OrderSubmitter(SimulatorBroker()).submit(order()).order_id
@pytest.mark.parametrize("kwargs",[{"quantity":0},{"limit_price":0},{"symbol":""}])
def test_submit_rejects_invalid(kwargs):
 with pytest.raises(ValueError):OrderSubmitter(SimulatorBroker()).submit(order(**kwargs))
def test_idempotency_caches_receipt():
 s=OrderSubmitter(SimulatorBroker());assert s.submit(order()) is s.submit(order())
def test_cancel_order():
 s=OrderSubmitter(SimulatorBroker());r=s.submit(order());assert s.cancel(r.order_id)
