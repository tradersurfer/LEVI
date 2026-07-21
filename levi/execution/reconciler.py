import threading,time
from levi.brokers.base import OrderStatus
class ContinuousReconciler:
    def __init__(self,broker,poll_interval=1):self.broker=broker;self.poll_interval=poll_interval;self._running=False;self._thread=None;self._callbacks=[];self._notified=set()
    def on_fill(self,oid,callback):self._callbacks.append((oid,callback))
    def start(self):
        if self._running:return
        self._running=True;self._thread=threading.Thread(target=self._run,daemon=True);self._thread.start()
    def stop(self):
        self._running=False
        if self._thread:self._thread.join(timeout=5)
    def _run(self):
        while self._running:
            for oid,callback in list(self._callbacks):
                if oid not in self._notified and self.broker.get_order_status(oid) is OrderStatus.FILLED:
                    callback(oid,self.broker.get_fills(oid));self._notified.add(oid)
            time.sleep(self.poll_interval)
