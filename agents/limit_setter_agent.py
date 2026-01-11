import json
import logging
import time
from datetime import datetime
from openai import AzureOpenAI
from config import settings

DEMO_MODE = True # Keep this for your presentation

try:
    azure_client = AzureOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
    )
    if not settings.AZURE_OPENAI_DEPLOYMENT_NAME:
        azure_client = None
        logging.warning("AZURE_OPENAI_DEPLOYMENT_NAME not found. AI summaries will be disabled.")
except Exception as e:
    azure_client = None
    logging.error(f"Failed to configure Azure OpenAI client: {e}")

class LimitSetterAgent:
    def __init__(self, agent_id="LimitSetter01"):
        self.agent_id = agent_id
        self.timestamp = datetime.now().isoformat()
        self.logger = logging.getLogger(self.agent_id)
        self.risk_scores = []
        self.policy_rules = {}
        self.erp_customer_map = {}

    def _perceive(self):
        self.logger.info("Perception phase: Loading data sources...")
        try:
            with open(settings.RISK_SCORE_FILE, 'r') as f:
                self.risk_scores = json.load(f)
            with open(settings.CREDIT_POLICY_FILE, 'r') as f:
                credit_policies = json.load(f)
                self.policy_rules = {rule['condition']: rule['action'] for rule in credit_policies['rules']}
            with open(settings.ERP_CUSTOMER_FILE, 'r') as f:
                erp_customers = json.load(f)
                self.erp_customer_map = {customer['customer_id']: customer for customer in erp_customers}
            self.logger.info("Successfully loaded all data sources.")
            return True
        except Exception as e:
            self.logger.error(f"Error in perception phase: {e}. Terminating.")
            return False

    def _generate_decision_summary_local(self, customer_id, risk_category, rule_applied, previous_limit, new_limit):
        self.logger.info(f"Generating summary for {customer_id} using LOCAL generator (Demo Mode)...")
        currency = "USD"
        if new_limit > previous_limit:
            increase_percent = round(((new_limit / previous_limit) - 1) * 100)
            summary = (f"The credit limit for {risk_category} Risk customer {customer_id} was increased by {increase_percent}% "
                       f"to {new_limit:,.2f} {currency} in accordance with the applied {rule_applied}.")
        else:
            summary = (f"In accordance with the {rule_applied}, the credit limit for {risk_category} Risk customer "
                       f"{customer_id} was reviewed and maintained at {previous_limit:,.2f} {currency}.")
        return summary

    def _generate_decision_summary(self, customer_id, risk_category, rule_applied, previous_limit, new_limit):
        if DEMO_MODE:
            return self._generate_decision_summary_local(customer_id, risk_category, rule_applied, previous_limit, new_limit)
        if not azure_client:
            return "Generative summary unavailable due to client configuration issue."
        
        system_prompt = "You are a professional Financial Risk Analyst writing a concise, one-sentence summary for an audit log."
        user_prompt = (f"Generate the summary for this event: "
                       f"Customer ID: {customer_id}, "
                       f"Risk Assessment: {risk_category} Risk, "
                       f"Policy Applied: {rule_applied}, "
                       f"Previous Limit: {previous_limit:,.2f} USD, "
                       f"New Limit: {new_limit:,.2f} USD.")
        try:
            self.logger.info(f"Generating summary for {customer_id} with Azure OpenAI (gpt-4o)...")
            response = azure_client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                max_tokens=100, temperature=0.7,
            )
            summary = response.choices[0].message.content.strip()
            return summary
        except Exception as e:
            self.logger.error(f"Azure OpenAI API call failed for {customer_id}: {e}")
            return "Automated summary generation failed; manual review may be required."
            
    def _write_to_unified_log(self, log_entry):
        """Reads the unified log, finds a matching workflow to append to, and writes back."""
        try:
            with open(settings.UNIFIED_LOG_FILE, 'r') as f:
                data = json.load(f)

            # Find the correct workflow based on customer_id and append the log
            log_appended = False
            for workflow in data.get("workflows", []):
                if workflow.get("customer_id") == log_entry.get("customer_id"):
                    # Ensure the 'logs' key exists and is a list
                    if "logs" not in workflow or not isinstance(workflow["logs"], list):
                        workflow["logs"] = []
                    workflow["logs"].append(log_entry)
                    log_appended = True
                    break
            
            # If no workflow for this customer exists, you might want to create one
            if not log_appended:
                self.logger.warning(f"No existing workflow found for {log_entry.get('customer_id')} in unified log. Log not appended.")

            with open(settings.UNIFIED_LOG_FILE, 'w') as f:
                json.dump(data, f, indent=2)

            if log_appended:
                self.logger.info(f"Successfully appended log for {log_entry['customer_id']} to unified log file.")
        except Exception as e:
            self.logger.error(f"Failed to write to unified log file: {e}")

    def _reason_and_decide(self):
        self.logger.info(f"Reasoning phase: Processing {len(self.risk_scores)} customers.")
        credit_limit_updates = []

        # Process all customers from the primary risk score input file
        for risk_data in self.risk_scores:
            customer_id = risk_data['customer_id']
            
            risk_category = risk_data.get('risk_category', 'Unknown')
            customer_info = self.erp_customer_map.get(customer_id)
            if not customer_info:
                self.logger.warning(f"Customer {customer_id} from risk score file not found in ERP data. Skipping.")
                continue
            
            current_limit = float(customer_info['current_limit'])
            new_limit = current_limit
            rule_applied = "No Matching Policy"
            validation_status = "PASS" # Assume PASS unless an error occurs

            action = self.policy_rules.get(risk_category)
            if action:
                rule_applied = f"{risk_category} Risk Policy"
                if "Increase limit by" in action:
                    try:
                        increase_percentage = float(action.split("by ")[1].replace('%', '')) / 100
                        new_limit = current_limit * (1 + increase_percentage)
                    except (ValueError, IndexError):
                        self.logger.error(f"Malformed action string for rule '{risk_category}': {action}")
                        validation_status = "FAIL"
            
            decision_summary = self._generate_decision_summary(
                customer_id, risk_category, rule_applied, current_limit, new_limit
            )
            
            credit_limit_updates.append({
                "customer_id": customer_id,
                "previous_limit": current_limit,
                "new_limit": round(new_limit, 2),
                "rule_applied": rule_applied,
                "decision_summary": decision_summary,
                "validation_status": validation_status,
                "timestamp": self.timestamp,
                "agent_id": self.agent_id
            })


            if not DEMO_MODE: time.sleep(3)
            else: time.sleep(1)

        return credit_limit_updates
        
    def _act(self, data):
        self.logger.info(f"Action phase: Writing results for {len(data)} customers to output file.")
        try:
            with open(settings.OUTPUT_FILE, 'w') as f:
                json.dump(data, f, indent=4)
            self.logger.info(f"Action successful. Output written to '{settings.OUTPUT_FILE}'.")
        except IOError as e:
            self.logger.error(f"Failed to write to output file: {e}.")

    def run(self):
        self.logger.info(f"--- Agent execution started ---")
        if self._perceive():
            decisions = self._reason_and_decide()
            if decisions:
                self._act(decisions)
        self.logger.info(f"--- Agent execution finished ---")