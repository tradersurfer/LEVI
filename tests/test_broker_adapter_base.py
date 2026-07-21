from dataclasses import FrozenInstanceError
from datetime import datetime,timezone
import pytest
from levi.brokers import *
from tests.broker_helpers import order,fill,pos
def test_broker_order_model(): assert order().quantity==1
def test_account_model(): assert Account("x",1,2,datetime.now(timezone.utc)).buying_power==2
def test_position_model(): assert pos().unrealized_pnl==2
def test_order_receipt_model(): assert OrderReceipt("1",OrderStatus.WORKING,"S",1,1,"call",datetime.now(timezone.utc)).status is OrderStatus.WORKING
def test_fill_model(): assert fill().fill_price==2.5
def test_models_immutable():
 with pytest.raises(FrozenInstanceError): order().quantity=2
