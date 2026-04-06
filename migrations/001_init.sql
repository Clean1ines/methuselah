-- 1. Пользователи
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    streak_days INTEGER DEFAULT 0,
    days_active INTEGER DEFAULT 0,
    last_entry_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Записи дня
CREATE TABLE IF NOT EXISTS daily_entries (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT REFERENCES users(telegram_id),
    entry_date DATE DEFAULT CURRENT_DATE,
    sleep FLOAT,
    energy INTEGER,
    mood INTEGER,
    activity VARCHAR(50),
    food VARCHAR(50),
    screen FLOAT,
    alcohol BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (telegram_id, entry_date)
);

-- 3. История инсайтов (для Anti-Repeat)
CREATE TABLE IF NOT EXISTS user_insight_history (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT REFERENCES users(telegram_id),
    rule_id VARCHAR(255),
    message_text TEXT,
    tone VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
