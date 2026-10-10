import bcrypt
import logging
from datetime import datetime
from database.connection import get_connection, is_db_connected

logger = logging.getLogger("database.users")

# In-memory session store / fallback registry for offline demonstration when MySQL service is starting up
_MEM_USERS = {}
_MEM_USER_ID_COUNTER = 1

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_user_by_email(email: str):
    """Retrieves user dict by email address using parameterized SQL query."""
    email_clean = email.strip().lower()
    if is_db_connected():
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE LOWER(email) = %s LIMIT 1", (email_clean,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return user
        except Exception as e:
            logger.error(f"Error querying user by email: {e}")
    
    # Fallback to memory registry if DB offline
    return _MEM_USERS.get(email_clean)

def register_user(full_name: str, email: str, password: str):
    """Registers a new user into MySQL with bcrypt password hashing."""
    global _MEM_USER_ID_COUNTER
    email_clean = email.strip().lower()
    full_name_clean = full_name.strip()

    if not full_name_clean:
        return False, "Full Name is required."
    if not email_clean or "@" not in email_clean:
        return False, "Please enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    existing = get_user_by_email(email_clean)
    if existing:
        return False, "An account with this email address already exists."

    pwd_hash = hash_password(password)

    if is_db_connected():
        try:
            conn = get_connection()
            cursor = conn.cursor()
            query = "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)"
            cursor.execute(query, (full_name_clean, email_clean, pwd_hash))
            conn.commit()
            new_id = cursor.lastrowid
            cursor.close()
            conn.close()
            logger.info(f"User registered in MySQL: {email_clean} (ID: {new_id})")
            return True, "Registration successful! You can now log in."
        except Exception as e:
            logger.error(f"MySQL error registering user: {e}")
            # fallthrough to memory fallback if DB fails

    # Memory fallback
    user_id = _MEM_USER_ID_COUNTER
    _MEM_USER_ID_COUNTER += 1
    _MEM_USERS[email_clean] = {
        "id": user_id,
        "full_name": full_name_clean,
        "email": email_clean,
        "password_hash": pwd_hash,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return True, "Registration successful (Offline Mode). You can now log in."

def authenticate_user(email: str, password: str):
    """Authenticates user email and password."""
    email_clean = email.strip().lower()
    user = get_user_by_email(email_clean)

    if not user:
        return False, "Invalid email or password.", None

    if verify_password(password, user["password_hash"]):
        user_info = {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
        }
        return True, "Login successful!", user_info
    else:
        return False, "Invalid email or password.", None
