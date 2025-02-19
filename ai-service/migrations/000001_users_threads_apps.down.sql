-- Drop index on `user_id` and `title`
DROP INDEX IF EXISTS idx_threads_user_id_title;

-- Drop `threads` table
DROP TABLE IF EXISTS threads;

-- Drop unique index on `username`
DROP INDEX IF EXISTS ix_users_username;

-- Drop unique index on `email`
DROP INDEX IF EXISTS ix_users_email;

-- Drop unique index on `username` and `email`
DROP INDEX IF EXISTS idx_users_username_email;

-- Drop `users` table
DROP TABLE IF EXISTS users;

-- Drop `connected_apps` table
DROP TABLE IF EXISTS connected_apps;
