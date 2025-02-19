CREATE TABLE IF NOT EXISTS users (
    id VARCHAR NOT NULL,
    created_by VARCHAR,
    created_at TIMESTAMP NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    username VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    PRIMARY KEY (id)
);

-- Create unique index on `username` and `email`
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_email ON users (username, email);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);


CREATE TABLE IF NOT EXISTS threads (
    id VARCHAR NOT NULL,
    created_by VARCHAR,
    created_at TIMESTAMP NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    user_id VARCHAR NOT NULL,
    title VARCHAR,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Create index on `user_id` and `title`
CREATE INDEX IF NOT EXISTS idx_threads_user_id_title ON threads (user_id, title);

CREATE TABLE IF NOT EXISTS connected_apps (
    id VARCHAR NOT NULL,
    created_by VARCHAR,
    created_at TIMESTAMP NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    user_id VARCHAR NOT NULL,
    app_name VARCHAR NOT NULL,
    connected_account_id VARCHAR NOT NULL,
    auth_value VARCHAR,
    auth_scheme VARCHAR,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);