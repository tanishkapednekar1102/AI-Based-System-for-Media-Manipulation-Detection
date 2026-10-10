-- SQL Script for AI-Based System for Media Manipulation Detection
-- Database Engine: MySQL 8.0+

CREATE DATABASE IF NOT EXISTS media_manipulation_detection;
USE media_manipulation_detection;

-- Table 1: users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table 2: detections
CREATE TABLE IF NOT EXISTS detections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    media_type VARCHAR(20) NOT NULL, -- IMAGE, VIDEO, AUDIO
    result VARCHAR(20) NOT NULL,     -- AUTHENTIC, MANIPULATED, SYNTHETIC, UNCERTAIN
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

-- Table 3: reports
CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    detection_id INT NOT NULL,
    report_path VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE,
    INDEX idx_detection_report (detection_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
