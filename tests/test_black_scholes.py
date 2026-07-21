import pytest
from levi.greeks import BlackScholesInputs,OptionType,calculate
def inputs(**kw): return BlackScholesInputs(**(dict(spot=100,strike=100,time_to_expiration_years=1,risk_free_rate=.05,volatility=.2,option_type=OptionType.CALL)|kw))
def test_call_value_known_range(): assert 10<calculate(inputs()).calculated_value<11
def test_put_value_known_range(): assert 5<calculate(inputs(option_type=OptionType.PUT)).calculated_value<6
def test_call_delta_range(): assert 0<calculate(inputs()).delta<1
def test_put_delta_range(): assert -1<calculate(inputs(option_type=OptionType.PUT)).delta<0
def test_gamma_positive(): assert calculate(inputs()).gamma>0
def test_vega_positive(): assert calculate(inputs()).vega_per_vol_point>0
def test_theta_call_negative(): assert calculate(inputs()).theta_per_day<0
def test_invalid_volatility_rejected():
 with pytest.raises(ValueError): inputs(volatility=0)
def test_expired_option_rejected():
 with pytest.raises(ValueError): inputs(time_to_expiration_years=0)
def test_liquidity_spread(): assert calculate(inputs(bid=1,ask=1.02)).liquid is True
