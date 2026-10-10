import logging
from datetime import datetime
from database.connection import get_connection, is_db_connected

logger = logging.getLogger("database.detections")

# In-memory detection cache fallback for offline testing
_MEM_DETECTIONS = []
_MEM_DETECTION_ID_COUNTER = 100

def save_detection(user_id: int, file_name: str, media_type: str, result: str,
                   confidence: float, manipulation_probability: float,
                   model_name: str, processing_time: float) -> int:
    """Stores media manipulation analysis result in MySQL database using parameterized query."""
    global _MEM_DETECTION_ID_COUNTER
    media_type_clean = media_type.upper().strip()
    result_clean = result.upper().strip()

    if is_db_connected():
        try:
            conn = get_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO detections 
                (user_id, file_name, media_type, result, confidence, manipulation_probability, model_name, processing_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                user_id, file_name, media_type_clean, result_clean,
                float(confidence), float(manipulation_probability),
                model_name, float(processing_time)
            ))
            conn.commit()
            detection_id = cursor.lastrowid
            cursor.close()
            conn.close()
            logger.info(f"Saved detection record {detection_id} to MySQL for user {user_id}")
            return detection_id
        except Exception as e:
            logger.error(f"Error saving detection to MySQL: {e}")

    # Fallback storage if DB offline
    det_id = _MEM_DETECTION_ID_COUNTER
    _MEM_DETECTION_ID_COUNTER += 1
    record = {
        "id": det_id,
        "user_id": user_id,
        "file_name": file_name,
        "media_type": media_type_clean,
        "result": result_clean,
        "confidence": float(confidence),
        "manipulation_probability": float(manipulation_probability),
        "model_name": model_name,
        "processing_time": float(processing_time),
        "created_at": datetime.now()
    }
    _MEM_DETECTIONS.insert(0, record)
    return det_id

def get_user_detections(user_id: int, media_filter: str = "ALL", result_filter: str = "ALL"):
    """Fetches user detection history from MySQL with filter options."""
    if is_db_connected():
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            sql = "SELECT * FROM detections WHERE user_id = %s"
            params = [user_id]

            if media_filter and media_filter.upper() != "ALL":
                sql += " AND media_type = %s"
                params.append(media_filter.upper())
            
            if result_filter and result_filter.upper() != "ALL":
                if result_filter.upper() == "AUTHENTIC":
                    sql += " AND result = 'AUTHENTIC'"
                elif result_filter.upper() == "MANIPULATED":
                    sql += " AND result IN ('MANIPULATED', 'SYNTHETIC')"
                else:
                    sql += " AND result = %s"
                    params.append(result_filter.upper())

            sql += " ORDER BY created_at DESC"
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"Error fetching user detections: {e}")

    # Memory fallback filtering
    results = [d for d in _MEM_DETECTIONS if d["user_id"] == user_id]
    if media_filter and media_filter.upper() != "ALL":
        results = [d for d in results if d["media_type"] == media_filter.upper()]
    if result_filter and result_filter.upper() != "ALL":
        rf = result_filter.upper()
        if rf == "AUTHENTIC":
            results = [d for d in results if d["result"] == "AUTHENTIC"]
        elif rf == "MANIPULATED":
            results = [d for d in results if d["result"] in ["MANIPULATED", "SYNTHETIC"]]
        else:
            results = [d for d in results if d["result"] == rf]
    return results

def get_detection_by_id(detection_id: int):
    """Retrieves single detection record details by ID."""
    if is_db_connected():
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM detections WHERE id = %s LIMIT 1", (detection_id,))
            record = cursor.fetchone()
            cursor.close()
            conn.close()
            if record:
                return record
        except Exception as e:
            logger.error(f"Error fetching detection {detection_id}: {e}")

    for d in _MEM_DETECTIONS:
        if d["id"] == detection_id:
            return d
    return None

def get_analytics_summary(user_id: int = None):
    """Calculates statistics and aggregated metrics directly from database records."""
    summary = {
        "total_analyses": 0,
        "authentic_count": 0,
        "manipulated_count": 0,
        "synthetic_count": 0,
        "uncertain_count": 0,
        "images_count": 0,
        "videos_count": 0,
        "audio_count": 0,
        "recent_detections": []
    }

    if is_db_connected():
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            where_clause = " WHERE user_id = %s" if user_id else ""
            params = (user_id,) if user_id else ()

            # Total & Counts
            cursor.execute(f"SELECT COUNT(*) AS cnt FROM detections{where_clause}", params)
            summary["total_analyses"] = cursor.fetchone()["cnt"]

            cursor.execute(f"SELECT COUNT(*) AS cnt FROM detections WHERE result = 'AUTHENTIC'" + (" AND user_id = %s" if user_id else ""), params)
            summary["authentic_count"] = cursor.fetchone()["cnt"]

            cursor.execute(f"SELECT COUNT(*) AS cnt FROM detections WHERE result = 'MANIPULATED'" + (" AND user_id = %s" if user_id else ""), params)
            summary["manipulated_count"] = cursor.fetchone()["cnt"]

            cursor.execute(f"SELECT COUNT(*) AS cnt FROM detections WHERE result = 'SYNTHETIC'" + (" AND user_id = %s" if user_id else ""), params)
            summary["synthetic_count"] = cursor.fetchone()["cnt"]

            cursor.execute(f"SELECT COUNT(*) AS cnt FROM detections WHERE result = 'UNCERTAIN'" + (" AND user_id = %s" if user_id else ""), params)
            summary["uncertain_count"] = cursor.fetchone()["cnt"]

            cursor.execute(f"SELECT COUNT(*) AS cnt FROM detections WHERE media_type = 'IMAGE'" + (" AND user_id = %s" if user_id else ""), params)
            summary["images_count"] = cursor.fetchone()["cnt"]

            cursor.execute(f"SELECT COUNT(*) AS cnt FROM detections WHERE media_type = 'VIDEO'" + (" AND user_id = %s" if user_id else ""), params)
            summary["videos_count"] = cursor.fetchone()["cnt"]

            cursor.execute(f"SELECT COUNT(*) AS cnt FROM detections WHERE media_type = 'AUDIO'" + (" AND user_id = %s" if user_id else ""), params)
            summary["audio_count"] = cursor.fetchone()["cnt"]

            # Recent 10 detections
            cursor.execute(f"SELECT * FROM detections{where_clause} ORDER BY created_at DESC LIMIT 10", params)
            summary["recent_detections"] = cursor.fetchall()

            cursor.close()
            conn.close()
            return summary
        except Exception as e:
            logger.error(f"Error computing analytics summary: {e}")

    # Fallback calculation over memory records
    records = [d for d in _MEM_DETECTIONS if user_id is None or d["user_id"] == user_id]
    summary["total_analyses"] = len(records)
    summary["authentic_count"] = sum(1 for r in records if r["result"] == "AUTHENTIC")
    summary["manipulated_count"] = sum(1 for r in records if r["result"] == "MANIPULATED")
    summary["synthetic_count"] = sum(1 for r in records if r["result"] == "SYNTHETIC")
    summary["uncertain_count"] = sum(1 for r in records if r["result"] == "UNCERTAIN")
    summary["images_count"] = sum(1 for r in records if r["media_type"] == "IMAGE")
    summary["videos_count"] = sum(1 for r in records if r["media_type"] == "VIDEO")
    summary["audio_count"] = sum(1 for r in records if r["media_type"] == "AUDIO")
    summary["recent_detections"] = records[:10]
    return summary
