# init_db.py
from models import init_db, SessionLocal, User
from utils import hash_password
from models import Student
init_db()
s = SessionLocal()
# create default admin if not exists
if not s.query(User).filter_by(username="admin").first():
    admin = User(username="admin", hashed_password=hash_password("admin123"), role="admin", display_name="Administrator")
    s.add(admin)
    s.commit()
print("DB initialized and admin user created (username: admin, password: admin123). Change password ASAP.")
s.close()
