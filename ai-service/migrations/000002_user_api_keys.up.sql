
CREATE TABLE IF NOT EXISTS user_api_keys (
    id VARCHAR NOT NULL,
    created_by VARCHAR,
    created_at TIMESTAMP NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    user_id VARCHAR NOT NULL,
    provider INTEGER NOT NULL,
    encrypted_value VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Create unique index on `user_id` and `provider_id`
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_api_keys_user_id_provider 
ON user_api_keys(user_id, provider);

-- Add column default_api_key_id to `users` table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS default_api_key_id VARCHAR;

-- Add foreign key constraint to `users` table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_users_default_api_key_id'
    ) THEN
        ALTER TABLE users 
        ADD CONSTRAINT fk_users_default_api_key_id 
        FOREIGN KEY (default_api_key_id) REFERENCES user_api_keys(id)
        ON DELETE SET NULL;
    END IF;
END $$;

-- Add column remain_trial_tokens to `users` table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS remain_trial_tokens INTEGER NOT NULL DEFAULT 0;


