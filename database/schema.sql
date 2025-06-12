-- Create conversation_history table
CREATE TABLE IF NOT EXISTS conversation_history (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,  -- Using UUID type
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',  -- Added metadata field
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_conversation_history_user_timestamp 
ON conversation_history(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_conversation_history_metadata 
ON conversation_history USING GIN (metadata);

-- Create user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL,  -- Using UUID type
    preferences JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id 
ON user_preferences(user_id);

-- Create RLS policies
ALTER TABLE conversation_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Policy for conversation_history
CREATE POLICY "Users can only access their own conversation history"
ON conversation_history
FOR ALL
USING (auth.uid() = user_id);

-- Policy for user_preferences
CREATE POLICY "Users can only access their own preferences"
ON user_preferences
FOR ALL
USING (auth.uid() = user_id);