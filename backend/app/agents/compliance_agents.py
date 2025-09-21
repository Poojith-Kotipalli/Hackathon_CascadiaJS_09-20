import autogen
from typing import Dict, List, Optional, Any
import json
import requests
from datetime import datetime
from .config import AgentConfig

class ComplianceAgents:
    """Individual specialized compliance checking agents"""
    
    def __init__(self):
        self.config = AgentConfig()
        self.backend_url = self.config.BACKEND_URL
        self.setup_agents()
        
    def setup_agents(self):
        """Initialize all specialized agents"""
        
        # 1. Product Classifier Agent - Routes to appropriate specialists
        self.classifier = autogen.AssistantAgent(
            name="ProductClassifier",
            system_message="""You are a product classification specialist for an e-commerce compliance system.
            
            Your task:
            1. Analyze the product name, description, and category
            2. Identify ALL potential compliance risks
            3. Determine which specialist agents should review this product
            
            Categories to consider:
            - CPSC: toys, children's products, furniture, household items
            - FDA_Food: food, beverages, dietary items, allergen concerns
            - FDA_Drug: supplements, health claims, medicines, vitamins
            - Electronics: devices with batteries, wireless, electrical components
            - Medical: medical devices, diagnostic tools, health monitors
            
            Respond in JSON format:
            {
                "product_type": "primary category",
                "risk_level": "critical/high/medium/low",
                "detected_concerns": ["list of specific concerns"],
                "recommended_agents": ["CPSC_Safety_Expert", "FDA_Food_Inspector", etc.],
                "reasoning": "brief explanation"
            }
            """,
            llm_config=self.config.LLM_CONFIG,
            human_input_mode="NEVER",
        )
        
        # 2. CPSC Safety Expert
        self.cpsc_agent = autogen.AssistantAgent(
            name="CPSC_Safety_Expert",
            system_message="""You are a CPSC (Consumer Product Safety Commission) compliance expert.
            
            Your expertise covers:
            - Lead paint violations (limit: 90 ppm for children's products)
            - Choking hazards (small parts for ages under 3)
            - Sharp edges and points
            - Strangulation risks (cords, strings)
            - Button battery safety
            - Toy safety standards (ASTM F963)
            - Furniture tip-over risks
            - Flammability standards
            
            When analyzing a product:
            1. Check against CPSC recall patterns
            2. Identify specific safety violations
            3. Assess severity (critical/high/medium/low)
            4. Provide specific regulatory citations when possible
            
            You will receive compliance data from the database to help your analysis.
            
            Respond in JSON format:
            {
                "violations_found": ["list of specific violations"],
                "severity": "critical/high/medium/low", 
                "recalled_similar_products": ["list of similar recalled items"],
                "recommended_actions": ["specific fixes needed"],
                "compliance_score": 0-100,
                "regulatory_citations": ["specific standards violated"]
            }
            """,
            llm_config=self.config.LLM_CONFIG,
            human_input_mode="NEVER",
        )
        
        # 3. FDA Food Inspector
        self.fda_food = autogen.AssistantAgent(
            name="FDA_Food_Inspector",
            system_message="""You are an FDA food safety and labeling compliance inspector.
            
            Your expertise covers:
            - Major allergens (milk, eggs, peanuts, tree nuts, wheat, soy, fish, shellfish, sesame)
            - Undeclared ingredients
            - Misleading health claims
            - Contamination risks
            - Proper nutrition labeling
            - GMO disclosure requirements
            - Organic certification claims
            
            Critical violations to check:
            1. Undeclared allergens (immediate recall)
            2. False health claims ("cures", "prevents disease")
            3. Contaminated ingredients
            4. Mislabeled ingredients
            
            You will receive FDA enforcement data to help your analysis.
            
            Respond in JSON format:
            {
                "violations_found": ["list of specific violations"],
                "allergen_risks": ["detected undeclared allergens"],
                "false_claims": ["misleading statements found"],
                "severity": "critical/high/medium/low",
                "compliance_score": 0-100,
                "fda_action_required": true/false
            }
            """,
            llm_config=self.config.LLM_CONFIG,
            human_input_mode="NEVER",
        )
        
        # 4. FDA Drug/Supplement Analyst
        self.fda_drug = autogen.AssistantAgent(
            name="FDA_Drug_Analyst", 
            system_message="""You are an FDA drug and dietary supplement compliance analyst.
            
            Your expertise covers:
            - Unapproved drug ingredients
            - False supplement claims (weight loss, muscle gain, sexual enhancement)
            - Hidden active pharmaceutical ingredients
            - Prescription drugs sold OTC
            - Banned substances (DMAA, ephedra, SARMs)
            - GMP violations
            - Misbranding
            
            Red flag claims to identify:
            - "Rapid weight loss" (>2 lbs/week)
            - "Increases muscle mass"
            - "Enhances sexual performance"
            - "Alternative to [prescription drug]"
            - "Cures/treats/prevents [disease]"
            
            You will receive FDA drug enforcement data to help your analysis.
            
            Respond in JSON format:
            {
                "violations_found": ["list of specific violations"],
                "banned_ingredients": ["list of prohibited substances"],
                "false_claims": ["unsubstantiated claims"],
                "hidden_drugs": ["undeclared pharmaceutical ingredients"],
                "severity": "critical/high/medium/low",
                "compliance_score": 0-100,
                "requires_prescription": true/false
            }
            """,
            llm_config=self.config.LLM_CONFIG,
            human_input_mode="NEVER",
        )
        
        # 5. Electronics Safety Expert
        self.electronics_agent = autogen.AssistantAgent(
            name="Electronics_Safety_Expert",
            system_message="""You are an electronics and electrical product safety compliance expert.
            
            Your expertise covers:
            - FCC Part 15 compliance (wireless devices)
            - UL certification requirements
            - Battery safety (UN38.3, IEC 62133)
            - EMI/EMC standards
            - Energy Star requirements
            - RoHS compliance (lead, mercury restrictions)
            - Lithium battery shipping regulations
            
            Critical safety checks:
            1. Uncertified high-voltage devices
            2. Missing FCC ID for wireless products
            3. Counterfeit certification marks
            4. Unsafe battery configurations
            5. Missing safety warnings
            
            Respond in JSON format:
            {
                "violations_found": ["list of specific violations"],
                "missing_certifications": ["required certs not found"],
                "safety_risks": ["electrical/fire/shock hazards"],
                "severity": "critical/high/medium/low",
                "compliance_score": 0-100,
                "required_markings": ["FCC ID", "UL mark", etc.]
            }
            """,
            llm_config=self.config.LLM_CONFIG,
            human_input_mode="NEVER",
        )
        
        # 6. Verdict Synthesizer - Combines all findings
        self.synthesizer = autogen.AssistantAgent(
            name="Compliance_Verdict_Synthesizer",
            system_message="""You are the chief compliance officer who synthesizes all specialist findings into a final verdict.
            
            Your responsibilities:
            1. Review all agent reports
            2. Calculate overall compliance score (weighted by severity)
            3. Determine final verdict: APPROVED / CONDITIONAL / REJECTED
            4. Prioritize critical violations
            5. Generate merchant action items
            
            Scoring weights:
            - Critical violations: -40 points each
            - High severity: -20 points each
            - Medium severity: -10 points each
            - Low severity: -5 points each
            
            Verdict criteria:
            - REJECTED: Score < 30 OR any critical safety violation
            - CONDITIONAL: Score 30-79, requires fixes before listing
            - APPROVED: Score 80-100, minor issues only
            
            Respond in JSON format:
            {
                "final_verdict": "APPROVED/CONDITIONAL/REJECTED",
                "overall_score": 0-100,
                "critical_violations": ["list most serious issues"],
                "total_violations": number,
                "agents_consulted": ["list of agents who reviewed"],
                "required_actions": ["prioritized list of fixes"],
                "estimated_compliance_time": "immediate/1-3 days/1 week/longer",
                "auto_report_to_agency": true/false,
                "similar_recalls_found": number,
                "confidence_level": "high/medium/low"
            }
            """,
            llm_config=self.config.LLM_CONFIG,
            human_input_mode="NEVER",
        )
    
    def call_backend_compliance_api(self, product_description: str, category: str = None) -> Dict:
        """Call your existing FastAPI compliance endpoint"""
        try:
            response = requests.post(
                f"{self.backend_url}/api/compliance/check",  # CHANGED: Added /api prefix
                json={
                    "text": product_description,  # CHANGED: "description" to "text" 
                    "check_type": "realtime"      # ADDED: check_type field
                },
                timeout=10
            )
        
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API returned {response.status_code}", "compliance_score": 0}
            
        except Exception as e:
            print(f"Error calling backend API: {e}")
            return {"error": str(e), "compliance_score": 0, "violations": []}   

# Add these methods to your existing ComplianceAgents class in compliance_agents.py

    def check_product_compliance(self, product: Dict) -> Dict:
        """Main method to orchestrate multi-agent compliance check"""
        
        start_time = datetime.now()
        
        # Initialize tracking
        agent_messages = []
        all_findings = {}
        
        try:
            # Step 1: Create UserProxy for orchestration
            user_proxy = autogen.UserProxyAgent(
                name="admin",
                system_message="Human admin coordinating compliance check.",
                code_execution_config=False,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=0
            )
            
            # Step 2: Format product info
            product_description = self._format_product_for_analysis(product)
            
            # Step 3: Get database compliance data (your existing backend)
            backend_data = self.call_backend_compliance_api(
                product.get('description', ''),
                product.get('category')
            )
            
            # Step 4: Classification first
            classification = self._classify_product(user_proxy, product_description, backend_data)
            all_findings['classification'] = classification
            
            # Step 5: Run specialist agents based on classification
            if classification and 'recommended_agents' in classification:
                specialist_results = self._run_specialist_agents(
                    user_proxy,
                    product_description,
                    classification['recommended_agents'],
                    backend_data
                )
                all_findings.update(specialist_results)
            
            # Step 6: Synthesize final verdict
            final_verdict = self._synthesize_verdict(user_proxy, all_findings)
            
            # Step 7: Compile results
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": final_verdict.get('final_verdict', 'PENDING'),
                "overall_score": final_verdict.get('overall_score', 0),
                "risk_level": classification.get('risk_level', 'unknown'),
                "violations": self._extract_all_violations(all_findings),
                "agents_consulted": list(all_findings.keys()),
                "required_actions": final_verdict.get('required_actions', []),
                "processing_time_ms": processing_time,
                "confidence_level": final_verdict.get('confidence_level', 'medium'),
                "backend_violations": backend_data.get('violations', []),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error in compliance check: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "status": "ERROR",
                "error": str(e),
                "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
            }
    
    def _format_product_for_analysis(self, product: Dict) -> str:
        """Format product data into a description string"""
        return f"""
        Product Name: {product.get('name', 'Unknown')}
        Description: {product.get('description', 'No description')}
        Category: {product.get('category', 'Uncategorized')}
        Price: ${product.get('price', 0)}
        Claims: {', '.join(product.get('claims', []))}
        Ingredients: {product.get('ingredients', 'Not specified')}
        Seller: {product.get('seller_id', 'Unknown')}
        """
    
    def _classify_product(self, user_proxy, product_description: str, backend_data: Dict) -> Dict:
        """Run classification agent"""
        try:
            # Prepare message with backend context
            message = f"""
            Please classify this product for compliance review:
            
            {product_description}
            
            Database compliance check found:
            Score: {backend_data.get('compliance_score', 'N/A')}
            Existing violations: {backend_data.get('violations', [])}
            """
            
            # Reset agents for fresh conversation
            self.classifier.reset()
            user_proxy.reset()
            
            # Run classification
            user_proxy.initiate_chat(
                self.classifier,
                message=message,
                max_turns=2,
                silent=True
            )
            
            # Extract JSON response
            response = user_proxy.last_message(self.classifier)
            return self._parse_agent_response(response)
            
        except Exception as e:
            print(f"Classification error: {e}")
            return {"risk_level": "high", "recommended_agents": ["CPSC_Safety_Expert", "FDA_Food_Inspector"]}
    
    def _run_specialist_agents(self, user_proxy, product_description: str, 
                             recommended_agents: List[str], backend_data: Dict) -> Dict:
        """Run recommended specialist agents"""
        specialist_results = {}
        
        agent_mapping = {
            "CPSC_Safety_Expert": self.cpsc_agent,
            "FDA_Food_Inspector": self.fda_food,
            "FDA_Drug_Analyst": self.fda_drug,
            "Electronics_Safety_Expert": self.electronics_agent
        }
        
        for agent_name in recommended_agents:
            if agent_name in agent_mapping:
                agent = agent_mapping[agent_name]
                
                try:
                    # Prepare specialist message
                    message = f"""
                    Please analyze this product for {agent_name.replace('_', ' ')} compliance:
                    
                    {product_description}
                    
                    Previous compliance data shows:
                    - Compliance score: {backend_data.get('compliance_score', 'N/A')}
                    - Known violations: {backend_data.get('violations', [])}
                    
                    Provide detailed compliance analysis.
                    """
                    
                    # Reset and run agent
                    agent.reset()
                    user_proxy.reset()
                    
                    user_proxy.initiate_chat(
                        agent,
                        message=message,
                        max_turns=2,
                        silent=True
                    )
                    
                    # Get response
                    response = user_proxy.last_message(agent)
                    specialist_results[agent_name] = self._parse_agent_response(response)
                    
                except Exception as e:
                    print(f"Error with {agent_name}: {e}")
                    specialist_results[agent_name] = {"error": str(e)}
        
        return specialist_results
    
    def _synthesize_verdict(self, user_proxy, all_findings: Dict) -> Dict:
        """Run synthesizer agent to create final verdict"""
        try:
            # Prepare synthesis message
            message = f"""
            Please synthesize the following compliance findings into a final verdict:
            
            Classification: {json.dumps(all_findings.get('classification', {}), indent=2)}
            
            Specialist Findings:
            {json.dumps({k: v for k, v in all_findings.items() if k != 'classification'}, indent=2)}
            
            Provide final compliance verdict and required actions.
            """
            
            # Reset and run synthesizer
            self.synthesizer.reset()
            user_proxy.reset()
            
            user_proxy.initiate_chat(
                self.synthesizer,
                message=message,
                max_turns=2,
                silent=True
            )
            
            response = user_proxy.last_message(self.synthesizer)
            return self._parse_agent_response(response)
            
        except Exception as e:
            print(f"Synthesis error: {e}")
            return {
                "final_verdict": "REJECTED",
                "overall_score": 0,
                "required_actions": ["Manual review required"],
                "confidence_level": "low"
            }
    
    def _parse_agent_response(self, response: Dict) -> Dict:
        """Parse JSON from agent response"""
        try:
            content = response.get("content", "{}")
            
            # Find JSON in the content
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            
            return {"raw_content": content}
            
        except Exception as e:
            print(f"Error parsing response: {e}")
            return {"parse_error": str(e), "raw_content": str(response)}
    
    def _extract_all_violations(self, all_findings: Dict) -> List[Dict]:
        """Extract all violations from all agent findings"""
        violations = []
        
        for agent_name, findings in all_findings.items():
            if isinstance(findings, dict) and 'violations_found' in findings:
                for violation in findings['violations_found']:
                    violations.append({
                        "agent": agent_name,
                        "violation": violation,
                        "severity": findings.get('severity', 'unknown')
                    })
        
        return violations