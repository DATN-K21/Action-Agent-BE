DROP INDEX IF EXISTS idx_users_username_email;

DROP INDEX IF EXISTS idx_threads_user_id_title;

CREATE INDEX IF NOT EXISTS idx_threads_user_id ON threads (user_id);