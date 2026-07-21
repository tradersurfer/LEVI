class OrderSubmitter:
    def __init__(self,client): self.client=client; self._submitted_orders={}
    def submit(self,order):
        if order.quantity<=0 or order.limit_price<=0 or not order.symbol.strip(): raise ValueError("invalid order")
        if order.idempotency_key and order.idempotency_key in self._submitted_orders:return self._submitted_orders[order.idempotency_key]
        r=self.client.submit_limit_order(order)
        if order.idempotency_key:self._submitted_orders[order.idempotency_key]=r
        return r
    def poll_status(self,oid):return self.client.get_order_status(oid)
    def cancel(self,oid):return self.client.cancel_order(oid)
