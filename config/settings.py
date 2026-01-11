import os
from dotenv import load_dotenv

# --- Step 1: Define and load the .env file ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Step 2: Securely access Azure OpenAI Credentials ---
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

# --- Step 3: Define all file and directory paths ---
RISK_SCORE_FILE = os.path.join(BASE_DIR, 'data', 'input', 'risk_score_output.json')
ERP_CUSTOMER_FILE = os.path.join(BASE_DIR, 'data', 'input', 'ERP_customer_master.json')
CREDIT_POLICY_FILE = os.path.join(BASE_DIR, 'config', 'credit_policy_rules.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'output', 'credit_limit_update.json')
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'agent.log')

# Input data paths
EXPOSURE_REPORT_FILE = os.path.join(BASE_DIR, 'data', 'input', 'aggregated_exposure_report.json')
# NOTE: The risk score filename is case-sensitive.
RISK_SCORE_FILE = os.path.join(BASE_DIR, 'data', 'input', 'Risk_score_output.json') 
ERP_CUSTOMER_FILE = os.path.join(BASE_DIR, 'data', 'input', 'ERP_customer_master.json')

# --- Additional paths for audit logging ---
# Path for the unified log file consumed by the Audit Logger
UNIFIED_LOG_FILE = os.path.join(BASE_DIR, 'data', 'input', 'all_agents_logs.json')

# Path for the final audit trail output
AUDIT_TRAIL_FILE = os.path.join(BASE_DIR, 'data', 'output', 'audit_trail.json')
