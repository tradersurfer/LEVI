import pytest
from levi.brokers.simulator import SimulatorBroker
from levi.execution.gateway import ExecutionGateway
from tests.broker_helpers import order
def gw():b=SimulatorBroker();b.authenticate({});return ExecutionGateway(b)
def test_disconnected():
 with pytest.raises(ValueError):ExecutionGateway(SimulatorBroker()).submit_order(order())
@pytest.mark.parametrize("kw",[{"quantity":0},{"limit_price":0}])
def test_invalid_values(kw):
 with pytest.raises(ValueError):gw().submit_order(order(**kw))
def test_tracking(): g=gw();r=g.submit_order(order());assert r.order_id in g._submitted_order_ids
def test_gateway_idempotency(): g=gw();assert g.submit_order(order()) is g.submit_order(order())
def test_cancel():g=gw();r=g.submit_order(order());assert g.cancel_order(r.order_id)
