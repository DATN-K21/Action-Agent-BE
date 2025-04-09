CREATE TABLE IF NOT EXISTS thread_files (
    id VARCHAR NOT NULL,
    created_by VARCHAR,
    created_at TIMESTAMP NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    url VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    size INTEGER NOT NULL,
    status INTEGER NOT NULL DEFAULT 0,
    error_message VARCHAR,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR NOT NULL,
    created_by VARCHAR,
    created_at TIMESTAMP NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    thread_id VARCHAR NOT NULL,
    content TEXT NOT NULL,
    format INTEGER NOT NULL DEFAULT 1,
    role INTEGER NOT NULL DEFAULT 0,
    question VARCHAR,
    choices VARCHAR,
    answer_idx INTEGER,
    file_id VARCHAR,
    PRIMARY KEY (id),
    FOREIGN KEY (thread_id) REFERENCES threads (id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES thread_files (id) ON DELETE CASCADE
);
