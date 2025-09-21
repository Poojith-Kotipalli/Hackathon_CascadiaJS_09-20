import autogen
from typing import Dict, List, Optional, Any
import json
import asyncio
from datetime import datetime
from .compliance_agents import ComplianceAgents
from .config import AgentConfig
import requests

class ComplianceOrchestrator:
    """Orchestrates multi-agent compliance checking conversations"""
    
    def __init__(self):
        self.config = AgentConfig()
        self.agents = ComplianceAgents()
        self.conversation_history = []
        self.token_usage = {"total": 0, "checks": 0}
        
    def create_user_proxy(self):
        """Create a user proxy that provides product info to agents"""
        return autogen.UserProxyAgent(
            name="ComplianceMonster",
            system_message="You are the compliance checking system coordinator.",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config=False,
        )
    
    def get_compliance_data_for_agent(self, agent_name: str, product: Dict) -> str:
        """Fetch relevant compliance data from your PostgreSQL database"""
        try:
            # Call your existing endpoint to get relevant violations
            response = requests.post(
                f"{self.config.BACKEND_URL}/compliance/check",
                json={
                    "description": product.get('description', ''),
                    "category": product.get('category', 'general')
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return f"""
                Database Search Results:
                - Similar violations found: {len(data.get('violations', []))}
                - Compliance score from RAG: {data.get('compliance_score', 0)}
                - Top matches: {json.dumps(data.get('violations', [])[:3])}
                """
            return "No database results available."
        except Exception as e:
            return f"Database search error: {str(e)}"
    
    def check_product_compliance(self, product: Dict) -> Dict:
        """
        Main orchestration function that coordinates agent discussion
        
        Args:
            product: Dict with keys: name, description, category, price, etc.
            
        Returns:
            Dict with complete compliance analysis and agent reasoning
        """
        
        # Initialize tracking
        start_time = datetime.now()
        agent_messages = []
        
        # Step 1: Classify the product
        user_proxy = self.create_user_proxy()
        
        # Create the classification message
        classification_request = f"""
        Please analyze this product for compliance:
        
        Product Name: {product.get('name', 'Unknown')}
        Description: {product.get('description', '')}
        Category: {product.get('category', 'general')}
        Price: ${product.get('price', 0)}
        Additional Info: {product.get('ingredients', '')} {product.get('warnings', '')}
        
        Determine which compliance checks are needed.
        """
        
        # Get classifier's analysis
        self.agents.classifier.reset()
        user_proxy.reset()
        
        user_proxy.initiate_chat(
            self.agents.classifier,
            message=classification_request,
            max_turns=2,
            silent=False
        )
        
        # Parse classifier response
        classifier_response = user_proxy.last_message(self.agents.classifier)
        
        try:
            # Extract JSON from the response
            content = classifier_response.get("content", "{}")
            # Find JSON in the content
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                classifier_data = json.loads(json_str)
            else:
                classifier_data = {}
            
            recommended_agents = classifier_data.get('recommended_agents', [])
            risk_level = classifier_data.get('risk_level', 'medium')
        except Exception as e:
            print(f"Error parsing classifier response: {e}")
            # Fallback if JSON parsing fails
            recommended_agents = self._determine_agents_by_keywords(product)
            risk_level = 'medium'
            classifier_data = {"error": "Failed to parse", "recommended_agents": recommended_agents}
        
        agent_messages.append({
            "agent": "ProductClassifier",
            "message": f"Product identified as {risk_level} risk. Activating {len(recommended_agents)} specialist agents.",
            "timestamp": datetime.now().isoformat(),
            "data": classifier_data
        })
        
        # Step 2: Create group chat with relevant agents
        agent_list = [user_proxy]
        agent_findings = {}
        
        # Process each recommended agent
        for agent_name in recommended_agents:
            current_agent = None
            
            if "CPSC" in agent_name:
                current_agent = self.agents.cpsc_agent
            elif "FDA_Food" in agent_name:
                current_agent = self.agents.fda_food
            elif "FDA_Drug" in agent_name:
                current_agent = self.agents.fda_drug
            elif "Electronics" in agent_name:
                current_agent = self.agents.electronics_agent
            
            if current_agent:
                # Get compliance data for this agent
                compliance_data = self.get_compliance_data_for_agent(agent_name, product)
                
                # Create specific check request
                check_request = f"""
                Please check this product for your domain of expertise:
                
                Product: {product.get('name')}
                Description: {product.get('description')}
                Category: {product.get('category')}
                Ingredients/Materials: {product.get('ingredients', 'Not specified')}
                
                {compliance_data}
                
                Provide your compliance analysis in JSON format.
                """
                
                # Reset agents for new conversation
                current_agent.reset()
                user_proxy.reset()
                
                # Get agent's analysis
                user_proxy.initiate_chat(
                    current_agent,
                    message=check_request,
                    max_turns=2,
                    silent=False
                )
                
                # Parse agent response
                agent_response = user_proxy.last_message(current_agent)
                
                try:
                    content = agent_response.get("content", "{}")
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        agent_data = json.loads(json_str)
                    else:
                        agent_data = {}
                    
                    agent_findings[agent_name] = agent_data
                    
                    agent_messages.append({
                        "agent": agent_name,
                        "message": f"Found {len(agent_data.get('violations_found', []))} violations",
                        "timestamp": datetime.now().isoformat(),
                        "data": agent_data
                    })
                except Exception as e:
                    print(f"Error parsing {agent_name} response: {e}")
                    agent_findings[agent_name] = {"error": "Failed to parse"}
                
                agent_list.append(current_agent)
        
        # Step 3: Synthesizer creates final verdict
        synthesis_request = f"""
        Based on the findings from all specialist agents, provide a final compliance verdict.
        
        Product: {product.get('name')}
        
        Agent Findings:
        {json.dumps(agent_findings, indent=2)}
        
        Provide your final verdict in JSON format.
        """
        
        self.agents.synthesizer.reset()
        user_proxy.reset()
        
        user_proxy.initiate_chat(
            self.agents.synthesizer,
            message=synthesis_request,
            max_turns=2,
            silent=False
        )
        
        # Parse synthesizer response
        synthesizer_response = user_proxy.last_message(self.agents.synthesizer)
        
        try:
            content = synthesizer_response.get("content", "{}")
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                final_verdict = json.loads(json_str)
            else:
                final_verdict = self._create_default_verdict(agent_findings)
        except Exception as e:
            print(f"Error parsing synthesizer response: {e}")
            final_verdict = self._create_default_verdict(agent_findings)
        
        # Step 4: Compile final results
        compliance_results = {
            "final_verdict": final_verdict.get("final_verdict", "CONDITIONAL"),
            "overall_score": final_verdict.get("overall_score", 50),
            "critical_violations": final_verdict.get("critical_violations", []),
            "total_violations": final_verdict.get("total_violations", 0),
            "agent_findings": agent_findings,
            "required_actions": final_verdict.get("required_actions", []),
            "product_name": product.get('name'),
            "product_id": product.get('id'),
            "check_timestamp": start_time.isoformat(),
            "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
            "agents_consulted": list(agent_findings.keys()),
            "risk_level": risk_level,
            "agent_reasoning_chain": agent_messages,
            "confidence_level": final_verdict.get("confidence_level", "medium")
        }
        
        # Update token usage tracking
        self.token_usage["checks"] += 1
        self.token_usage["total"] += len(recommended_agents) * 800  # Estimate
        
        # Store conversation for analysis
        self.conversation_history.append({
            "product": product,
            "results": compliance_results,
            "timestamp": datetime.now().isoformat()
        })
        
        return compliance_results
    
    def _determine_agents_by_keywords(self, product: Dict) -> List[str]:
        """Fallback method to determine agents by keyword matching"""
        agents_to_activate = []
        product_text = f"{product.get('name', '')} {product.get('description', '')} {product.get('category', '')}".lower()
        
        agent_triggers = {
            "CPSC_Safety_Expert": ["toy", "child", "play", "baby", "game", "lead", "paint"],
            "FDA_Food_Inspector": ["food", "eat", "drink", "allergen", "ingredient", "organic"],
            "FDA_Drug_Analyst": ["supplement", "vitamin", "pill", "weight", "muscle", "health"],
            "Electronics_Safety_Expert": ["electronic", "battery", "charger", "wireless", "bluetooth"]
        }
        
        for agent_name, keywords in agent_triggers.items():
            if any(keyword in product_text for keyword in keywords):
                agents_to_activate.append(agent_name)
        
        # Always have at least one agent
        if not agents_to_activate:
            agents_to_activate.append("CPSC_Safety_Expert")
            
        return agents_to_activate
    
    def _create_default_verdict(self, agent_findings: Dict) -> Dict:
        """Create a default verdict if parsing fails"""
        total_violations = sum(
            len(findings.get("violations_found", [])) 
            for findings in agent_findings.values()
        )
        
        score = max(0, 100 - (total_violations * 15))
        
        if score < 30:
            verdict = "REJECTED"
        elif score < 80:
            verdict = "CONDITIONAL"
        else:
            verdict = "APPROVED"
        
        return {
            "final_verdict": verdict,
            "overall_score": score,
            "total_violations": total_violations,
            "critical_violations": [],
            "required_actions": ["Review all violations and fix before listing"],
            "confidence_level": "low"
        }
    
    def get_token_usage(self) -> Dict:
        """Get current token usage statistics"""
        return {
            "total_tokens": self.token_usage["total"],
            "total_checks": self.token_usage["checks"],
            "estimated_cost": (self.token_usage["total"] / 1000000) * 0.15  # $0.15 per 1M tokens
        }