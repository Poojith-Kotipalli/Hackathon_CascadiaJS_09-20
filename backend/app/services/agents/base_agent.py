from dataclasses import dataclass
from typing import Dict, Any, Optional
from ..compliance_engine import ComplianceEngine

@dataclass
class AgentResult:
    name: str
    table: Optional[str]
    report: Dict[str, Any]

class BaseComplianceAgent:
    def __init__(self, name: str, table: Optional[str] = None):
        self.name = name
        self.table = table
        self.engine = ComplianceEngine()

    async def run(self, text: str, check_type: str | None = None) -> AgentResult:
        res = await self.engine.analyze(text=text, check_type=check_type, table=self.table)
        return AgentResult(name=self.name, table=self.table, report=res)
