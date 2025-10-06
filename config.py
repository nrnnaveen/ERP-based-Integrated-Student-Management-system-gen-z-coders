# config.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("COLLEGE_ERP_DB_PATH", os.path.join(BASE_DIR, "college_erp.db"))
SECRET_KEY = os.environ.get("COLLEGE_ERP_SECRET", "change_this_to_a_strong_random_string")
RECEIPTS_FOLDER = os.environ.get("RECEIPTS_FOLDER", os.path.join(BASE_DIR, "receipts"))
BACKUP_FOLDER = os.environ.get("BACKUP_FOLDER", os.path.join(BASE_DIR, "backups"))

# Make sure folders exist
os.makedirs(RECEIPTS_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)
