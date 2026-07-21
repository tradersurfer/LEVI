from datetime import datetime, timezone
class PositionTracker:
    def __init__(self,client):self.client=client;self._positions={};self._last_sync=None
    def sync_positions(self):
        p=self.client.get_positions();self._positions={x.symbol:x for x in p};self._last_sync=datetime.now(timezone.utc);return p
    def get_position(self,symbol):return self._positions.get(symbol)
    def get_daily_pnl(self):return sum(p.unrealized_pnl for p in self._positions.values())
    def get_realized_pnl(self):return sum(p.realized_pnl for p in self._positions.values())
    def get_total_daily_pnl(self):return self.get_daily_pnl()+self.get_realized_pnl()
