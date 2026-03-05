CREATE TABLE sessions (
    session_id VARCHAR(50) PRIMARY KEY,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    final_score INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'IN_PROGRESS'
);

CREATE TABLE vr_events (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES sessions(session_id),
    event_timestamp TIMESTAMP,
    scene_id INT,
    event_type VARCHAR(50),
    payload JSONB,
    telemetry JSONB
);

CREATE INDEX idx_vr_events_session_time ON vr_events(session_id, event_timestamp);
