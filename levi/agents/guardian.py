from levi.risk.guardian_rules import GuardianDecision,GuardianRules,TradeRiskRequest
class GuardianAgent:
    agent_name="GUARDIAN"
    def __init__(self,rules=None): self.rules=rules or GuardianRules()
    def analyze(self,request:TradeRiskRequest)->GuardianDecision: return self.rules.evaluate(request)
