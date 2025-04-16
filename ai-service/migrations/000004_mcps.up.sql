CREATE TABLE IF NOT EXISTS connected_mcps (
    id VARCHAR NOT NULL,
    created_by VARCHAR,
    created_at TIMESTAMP NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    user_id VARCHAR NOT NULL,
    mcp_name VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    connection_type VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS connected_mcps_user_id_mcp_name_idx ON connected_mcps (user_id, mcp_name);