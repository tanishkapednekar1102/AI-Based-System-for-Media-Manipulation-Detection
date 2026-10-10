import logging
from database.connection import get_connection, is_db_connected

logger = logging.getLogger("database.reports")

_MEM_REPORTS = {}

def save_report_metadata(detection_id: int, report_path: str) -> bool:
    """Saves PDF report metadata linked to a detection ID into MySQL."""
    if is_db_connected():
        try:
            conn = get_connection()
            cursor = conn.cursor()
            query = "INSERT INTO reports (detection_id, report_path) VALUES (%s, %s)"
            cursor.execute(query, (detection_id, report_path))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving report metadata to MySQL: {e}")

    _MEM_REPORTS[detection_id] = report_path
    return True

def get_report_by_detection_id(detection_id: int):
    """Retrieves PDF report path by detection ID."""
    if is_db_connected():
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM reports WHERE detection_id = %s ORDER BY created_at DESC LIMIT 1", (detection_id,))
            record = cursor.fetchone()
            cursor.close()
            conn.close()
            if record:
                return record["report_path"]
        except Exception as e:
            logger.error(f"Error fetching report path for detection {detection_id}: {e}")

    return _MEM_REPORTS.get(detection_id)
