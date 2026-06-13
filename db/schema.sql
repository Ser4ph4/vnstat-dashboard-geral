-- vnstat dashboard schema
CREATE DATABASE IF NOT EXISTS vnstat_dash CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE vnstat_dash;

-- Users table for dashboard login
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hosts registry
CREATE TABLE IF NOT EXISTS hosts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(64) NOT NULL UNIQUE, -- e.g. "pi", "note", "ser4ph-arm"
    display_name VARCHAR(128) NOT NULL,
    tailscale_ip VARCHAR(45),
    interface VARCHAR(32) DEFAULT 'eth0',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP NULL
);

-- Traffic snapshots — one row per host per hour
CREATE TABLE IF NOT EXISTS traffic_snapshots (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    host_id INT NOT NULL,
    captured_at TIMESTAMP NOT NULL,
    -- Hourly totals
    rx_bytes BIGINT DEFAULT 0,
    tx_bytes BIGINT DEFAULT 0,
    -- Cumulative totals from vnstat
    rx_total BIGINT DEFAULT 0,
    tx_total BIGINT DEFAULT 0,
    -- Rate at capture time (bytes/s)
    rx_rate BIGINT DEFAULT 0,
    tx_rate BIGINT DEFAULT 0,
    INDEX idx_host_time (host_id, captured_at),
    INDEX idx_captured_at (captured_at),
    FOREIGN KEY (host_id) REFERENCES hosts (id) ON DELETE CASCADE
);

-- Daily aggregates (pre-computed for fast queries)
CREATE TABLE IF NOT EXISTS traffic_daily (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    host_id INT NOT NULL,
    day DATE NOT NULL,
    rx_bytes BIGINT DEFAULT 0,
    tx_bytes BIGINT DEFAULT 0,
    UNIQUE KEY uq_host_day (host_id, day),
    INDEX idx_day (day),
    FOREIGN KEY (host_id) REFERENCES hosts (id) ON DELETE CASCADE
);

-- Monthly aggregates
CREATE TABLE IF NOT EXISTS traffic_monthly (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    host_id INT NOT NULL,
    year SMALLINT NOT NULL,
    month TINYINT NOT NULL,
    rx_bytes BIGINT DEFAULT 0,
    tx_bytes BIGINT DEFAULT 0,
    UNIQUE KEY uq_host_month (host_id, year, month),
    FOREIGN KEY (host_id) REFERENCES hosts (id) ON DELETE CASCADE
);

-- Seed default hosts
INSERT INTO
    hosts (
        name,
        display_name,
        tailscale_ip,
        interface
    )
VALUES (
        'pi',
        'Raspberry Pi',
        '100.x.x.1',
        'eth0'
    ),
    (
        'note',
        'Note (Debian)',
        '100.x.x.2',
        'wlx503eaa8913bf'
    ),
    (
        'ser4ph-arm',
        'Oracle ARM VPS',
        '100.x.x.3',
        'enp0s6'
    )
ON DUPLICATE KEY UPDATE
    display_name = VALUES(display_name);

-- Default admin user (password: changeme — hashed with bcrypt)
-- Run: python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('changeme'))"
-- and replace below, or let the app seed it on first run