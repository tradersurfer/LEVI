from levi.greeks.black_scholes import BlackScholesInputs, BlackScholesResult, calculate
class VoltAgent:
    agent_name="VOLT"
    def analyze(self,inputs:BlackScholesInputs)->BlackScholesResult: return calculate(inputs)
