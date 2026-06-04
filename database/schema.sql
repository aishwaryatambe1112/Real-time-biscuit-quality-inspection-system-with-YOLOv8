-- ============================================================
-- Real-Time Biscuit Quality Inspection System
-- MySQL Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS biscuit_inspection
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE biscuit_inspection;

-- ── Users ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email        VARCHAR(255) NOT NULL UNIQUE,
    name         VARCHAR(120) NOT NULL,
    role         ENUM('admin','operator') NOT NULL DEFAULT 'operator',
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB;

-- ── OTP store (short-lived) ───────────────────────────────
CREATE TABLE IF NOT EXISTS otp_tokens (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email       VARCHAR(255) NOT NULL,
    otp_hash    VARCHAR(64)  NOT NULL,   -- SHA-256 of OTP
    expires_at  DATETIME     NOT NULL,
    used        BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email_exp (email, expires_at)
) ENGINE=InnoDB;

-- ── Inspection batches ────────────────────────────────────
CREATE TABLE IF NOT EXISTS batches (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id       INT UNSIGNED NOT NULL,
    brand         ENUM('Monaco','Parle-G','Marie') NOT NULL,
    started_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at      DATETIME,
    total_count   INT UNSIGNED NOT NULL DEFAULT 0,
    good_count    INT UNSIGNED NOT NULL DEFAULT 0,
    broken_count  INT UNSIGNED NOT NULL DEFAULT 0,
    burnt_count   INT UNSIGNED NOT NULL DEFAULT 0,
    notes         TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_brand     (brand),
    INDEX idx_started   (started_at),
    INDEX idx_user      (user_id)
) ENGINE=InnoDB;

-- ── Individual detection events ───────────────────────────
CREATE TABLE IF NOT EXISTS detections (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    batch_id        INT UNSIGNED NOT NULL,
    biscuit_index   TINYINT UNSIGNED NOT NULL DEFAULT 1,  -- 1 or 2 (pair position)
    brand           ENUM('Monaco','Parle-G','Marie') NOT NULL,
    quality         ENUM('Good','Broken','Burnt') NOT NULL,
    confidence      DECIMAL(5,4) NOT NULL,
    bbox_x1         FLOAT,
    bbox_y1         FLOAT,
    bbox_x2         FLOAT,
    bbox_y2         FLOAT,
    inference_ms    FLOAT,
    detected_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE CASCADE,
    INDEX idx_batch      (batch_id),
    INDEX idx_brand_qual (brand, quality),
    INDEX idx_detected   (detected_at)
) ENGINE=InnoDB;

-- ── Hourly aggregated stats (for fast dashboard queries) ──
CREATE TABLE IF NOT EXISTS hourly_stats (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand           ENUM('Monaco','Parle-G','Marie') NOT NULL,
    hour_bucket     DATETIME NOT NULL,          -- truncated to hour
    total_count     INT UNSIGNED NOT NULL DEFAULT 0,
    good_count      INT UNSIGNED NOT NULL DEFAULT 0,
    broken_count    INT UNSIGNED NOT NULL DEFAULT 0,
    burnt_count     INT UNSIGNED NOT NULL DEFAULT 0,
    UNIQUE KEY uq_brand_hour (brand, hour_bucket),
    INDEX idx_hour_bucket (hour_bucket)
) ENGINE=InnoDB;

-- ── Stored procedure: upsert hourly stats ─────────────────
DELIMITER $$

CREATE PROCEDURE IF NOT EXISTS upsert_hourly_stats(
    IN p_brand    VARCHAR(20),
    IN p_quality  VARCHAR(10),
    IN p_ts       DATETIME
)
BEGIN
    DECLARE v_bucket DATETIME;
    SET v_bucket = DATE_FORMAT(p_ts, '%Y-%m-%d %H:00:00');

    INSERT INTO hourly_stats (brand, hour_bucket, total_count, good_count, broken_count, burnt_count)
    VALUES (p_brand, v_bucket, 1,
            IF(p_quality='Good', 1, 0),
            IF(p_quality='Broken', 1, 0),
            IF(p_quality='Burnt', 1, 0))
    ON DUPLICATE KEY UPDATE
        total_count   = total_count + 1,
        good_count    = good_count   + IF(p_quality='Good', 1, 0),
        broken_count  = broken_count + IF(p_quality='Broken', 1, 0),
        burnt_count   = burnt_count  + IF(p_quality='Burnt', 1, 0);
END$$

DELIMITER ;

-- ── Seed admin user (change email/name as needed) ─────────
INSERT IGNORE INTO users (email, name, role)
VALUES ('admin@biscuitai.com', 'System Admin', 'admin');
