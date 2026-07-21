from levi.brokers.models import OrderSide,OrderType
class ExecutionGateway:
    def __init__(self,broker):self.broker=broker;self._submitted_order_ids=set();self._idempotency={}
    def submit_order(self,order):
        if not self.broker.is_connected():raise ValueError("Broker not connected")
        if order.side not in (OrderSide.CALL,OrderSide.PUT):raise ValueError("options calls/puts only")
        if order.quantity<=0:raise ValueError("quantity must be > 0")
        if order.limit_price<=0:raise ValueError("limit_price must be > 0")
        if order.order_type is not OrderType.LIMIT:raise ValueError("only LIMIT orders allowed")
        if order.idempotency_key and order.idempotency_key in self._idempotency:return self._idempotency[order.idempotency_key]
        r=self.broker.submit_order(order);self._submitted_order_ids.add(r.order_id)
        if order.idempotency_key:self._idempotency[order.idempotency_key]=r
        return r
    def cancel_order(self,oid):return self.broker.cancel_order(oid)
