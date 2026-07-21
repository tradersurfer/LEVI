from levi.brokers.tastytrade.positions import PositionTracker
from tests.broker_helpers import pos
class C:
 def get_positions(self):return [pos()]
def test_sync_positions(): assert PositionTracker(C()).sync_positions()
def test_get_position(): p=PositionTracker(C());p.sync_positions();assert p.get_position("SPY")
def test_unrealized_pnl(): p=PositionTracker(C());p.sync_positions();assert p.get_daily_pnl()==2
def test_total_pnl(): p=PositionTracker(C());p.sync_positions();assert p.get_total_daily_pnl()==3
