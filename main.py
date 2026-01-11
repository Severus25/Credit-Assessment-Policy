import logging
import os
from agents.merger_agent import MergerAgent           # <-- NEW
from agents.limit_setter_agent import LimitSetterAgent
from agents.audit_logger_agent import AuditLoggerAgent
from config import settings

def setup_logging():
    """Configures logging to output to both console and a file."""
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        handlers=[
            logging.FileHandler(settings.LOG_FILE, mode='w'), # Overwrite log file on each run
            logging.StreamHandler()
        ]
    )

def main():
    """
    Main function to orchestrate the full credit assessment workflow.
    It runs the agents in a logical sequence to produce the final audit trail.
    """
    setup_logging()
    logger = logging.getLogger("WorkflowOrchestrator")
    
    logger.info("==========================================================")
    logger.info("=== STARTING CUSTOMER CREDIT ASSESSMENT PROCESS WORKFLOW ===")
    logger.info("==========================================================")
    
    # --- STAGE 1: Run the Limit Setter Agent ---
    # This agent runs first to generate its primary output.
    logger.info("\n>>> STAGE 1: EXECUTING LIMIT SETTER AGENT...")
    limit_agent = LimitSetterAgent()
    limit_agent.run()
    logger.info(">>> STAGE 1: LIMIT SETTER AGENT FINISHED.\n")

    # --- STAGE 2: Run the Merger Agent ---
    # This agent simulates the upstream process and merges all outputs
    # (including the one just created by the Limit Setter) into a single log file.
    logger.info(">>> STAGE 2: EXECUTING MERGER AGENT to create unified log...")
    merger = MergerAgent()
    merger.run()
    logger.info(">>> STAGE 2: MERGER AGENT FINISHED.\n")

    # --- STAGE 3: Run the Audit Logger Agent ---
    # This final agent consumes the unified log file to produce the audit trail.
    logger.info(">>> STAGE 3: EXECUTING AUDIT LOGGER AGENT...")
    audit_agent = AuditLoggerAgent()
    audit_agent.run()
    logger.info(">>> STAGE 3: AUDIT LOGGER AGENT FINISHED.\n")

    logger.info("======================================================")
    logger.info("=== WORKFLOW FINISHED. ALL STAGES EXECUTED. ===")
    logger.info("======================================================")

if __name__ == '__main__':
    main()
