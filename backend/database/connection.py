import logging
import mysql.connector
from mysql.connector import errorcode

try:
    from backend import config
except ImportError:
    import config

logger = logging.getLogger("database.connection")

_db_available = False
_db_pool = None

def get_raw_connection(with_db=True):
    """Establishes direct connection to MySQL server."""
    kwargs = {
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
        "autocommit": True
    }
    if with_db:
        kwargs["database"] = config.DB_NAME
    return mysql.connector.connect(**kwargs)

def init_db():
    """Initializes MySQL database and creates tables automatically if not present."""
    global _db_available
    try:
        # Step 1: Connect without database to ensure DB exists
        conn = get_raw_connection(with_db=False)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` DEFAULT CHARACTER SET utf8mb4;")
        cursor.close()
        conn.close()

        # Step 2: Connect with database and create tables
        conn = get_raw_connection(with_db=True)
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_email (email)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Create detections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                file_name VARCHAR(255) NOT NULL,
                media_type VARCHAR(20) NOT NULL,
                result VARCHAR(20) NOT NULL,
                confidence FLOAT NOT NULL,
                manipulation_probability FLOAT NOT NULL,
                model_name VARCHAR(100) NOT NULL,
                processing_time FLOAT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_detections (user_id),
                INDEX idx_media_type (media_type),
                INDEX idx_result (result)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Create reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                detection_id INT NOT NULL,
                report_path VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE,
                INDEX idx_detection_report (detection_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.close()
        conn.close()
        _db_available = True
        logger.info("MySQL database initialized successfully.")
        return True, "Database initialized successfully"
    except mysql.connector.Error as err:
        _db_available = False
        err_msg = f"MySQL Connection Error [{err.errno}]: {err.msg}"
        logger.warning(err_msg)
        return False, err_msg
    except Exception as e:
        _db_available = False
        err_msg = f"Database Connection Exception: {str(e)}"
        logger.warning(err_msg)
        return False, err_msg

def is_db_connected():
    """Checks if MySQL database is active."""
    global _db_available
    if not _db_available:
        status, _ = init_db()
        return status
    return True

def get_connection():
    """Helper to retrieve an active database connection."""
    if not is_db_connected():
        raise mysql.connector.Error(msg="MySQL service is not available or credentials in .env are invalid.")
    return get_raw_connection(with_db=True)
