import json
import logging
from config import settings

class AuditLoggerAgent:
    """
    An agent that processes a unified log file from all other agents
    to create a final, summarized audit trail for each workflow.
    """
    AGENT_TO_STEP = {
        "ExposureAggregator01": "Exposure Aggregation",
        "RiskScoring01": "Risk Scoring",
        "LimitSetter01": "Limit Setting",
        "ComplianceChecker01": "Compliance Check" # For future-proofing
    }

    WORKFLOW_ORDER = [
        "Exposure Aggregation",
        "Risk Scoring",
        "Limit Setting",
        "Compliance Check"
    ]

    def __init__(self, agent_id="AuditLogger01"):
        self.agent_id = agent_id
        self.logger = logging.getLogger(self.agent_id)
        self.input_file = settings.UNIFIED_LOG_FILE
        self.output_file = settings.AUDIT_TRAIL_FILE

    def _process_single_workflow(self, workflow):
        """Processes the logs for one workflow to create a summary."""
        executed_steps = {}
        overall_status = "PASS"

        for log in workflow.get("logs", []):
            step = self.AGENT_TO_STEP.get(log.get("agent_id"))
            if step:
                executed_steps[step] = log.get("timestamp")

            if log.get("validation_status", "FAIL") != "PASS":
                overall_status = "FAIL"

        events = []
        for step in self.WORKFLOW_ORDER:
            if step in executed_steps:
                events.append({
                    "step": step,
                    "status": "Completed",
                    "timestamp": executed_steps[step]
                })

        return {
            "workflow_id": workflow.get("workflow_id"),
            "customer_id": workflow.get("customer_id"),
            "events": events,
            "final_status": overall_status
        }

    def run(self):
        """Main execution method for the Audit Logger Agent."""
        self.logger.info("--- Agent execution started ---")
        try:
            with open(self.input_file, "r") as f:
                data = json.load(f)

            audit_trails = []
            for workflow in data.get("workflows", []):
                audit_trails.append(self._process_single_workflow(workflow))

            with open(self.output_file, "w") as f:
                json.dump(audit_trails, f, indent=4)

            self.logger.info(f"Action successful. Audit trails for {len(audit_trails)} workflows written to '{self.output_file}'.")

        except FileNotFoundError:
            self.logger.error(f"Critical data source not found: {self.input_file}. Terminating.")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

        self.logger.info("--- Agent execution finished ---")
