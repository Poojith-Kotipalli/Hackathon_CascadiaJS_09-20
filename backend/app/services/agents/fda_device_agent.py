from .base_agent import BaseComplianceAgent
class FDA_Device_Agent(BaseComplianceAgent):
    def __init__(self): super().__init__("FDA_Device_Agent", "fda_device_data")
