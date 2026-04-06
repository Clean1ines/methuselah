from app.infrastructure.database import Database
from app.domain.models import User, DailyEntry
from datetime import datetime, timedelta
from typing import List, Union
import asyncpg

class UserRepository:
    """Handles User aggregate retrieval and streak business-logic update safely."""
    @staticmethod
    async def get_or_create(telegram_id: int) -> User:
        if Database.pool is None:
            raise RuntimeError("Database pool uninitialized")
            
        async with Database.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1", telegram_id
            )
            
            if row:
                user = User(
                    telegram_id=row['telegram_id'],
                    streak_days=row['streak_days'],
                    days_active=row['days_active'],
                    last_entry_at=row['last_entry_at']
                )

                user = await UserRepository._update_streak_logic(user, conn)

                if user.last_entry_at:
                    delta = datetime.now().date() - user.last_entry_at.date()
                    user.gap_days = delta.days
                else:
                    user.gap_days = 0

                return user
            
            await conn.execute(
                "INSERT INTO users (telegram_id) VALUES ($1)", telegram_id
            )
            user = User(telegram_id=telegram_id)
            user.gap_days = 0
            return user

    @staticmethod
    async def _update_streak_logic(user: User, conn: asyncpg.Connection) -> User:
        """Executes idempotent streak resolution internally."""
        if not user.last_entry_at:
            return user

        today = datetime.now().date()
        last_date = user.last_entry_at.date()

        if last_date == today:
            return user
        
        if last_date == today - timedelta(days=1):
            user.streak_days += 1
        else:
            user.streak_days = 1
            
        user.days_active += 1
        
        await conn.execute(
            """UPDATE users SET streak_days = $1, days_active = $2, last_entry_at = NOW() 
               WHERE telegram_id = $3""", 
            user.streak_days, user.days_active, user.telegram_id
        )
        return user


class EntryRepository:
    """Handles persistence of daily metrics ensuring idempotency via UPSERT."""
    @staticmethod
    async def save_entry(entry: DailyEntry) -> None:
        if Database.pool is None:
            raise RuntimeError("Database pool uninitialized")
            
        async with Database.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO daily_entries 
                (telegram_id, entry_date, sleep, energy, mood, activity, food, screen, alcohol)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (telegram_id, entry_date) DO UPDATE SET
                sleep = EXCLUDED.sleep,
                energy = EXCLUDED.energy,
                mood = EXCLUDED.mood,
                activity = EXCLUDED.activity,
                food = EXCLUDED.food,
                screen = EXCLUDED.screen,
                alcohol = EXCLUDED.alcohol""",
                entry.telegram_id, entry.entry_date, entry.sleep, entry.energy, entry.mood,
                entry.activity, entry.food, entry.screen, entry.alcohol
            )
            await conn.execute(
                "UPDATE users SET last_entry_at = NOW() WHERE telegram_id = $1",
                entry.telegram_id
            )


class InsightHistoryRepository:
    """Stores full texts preventing anti-pattern overlaps."""
    @staticmethod
    async def get_recent_insights(telegram_id: int, limit: int = 10) -> List[asyncpg.Record]:
        if Database.pool is None:
            raise RuntimeError("Database pool uninitialized")
            
        async with Database.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT rule_id, message_text FROM user_insight_history 
                   WHERE telegram_id = $1 
                   ORDER BY created_at DESC LIMIT $2""", 
                telegram_id, limit
            )
            return list(rows)

    @staticmethod
    async def save_insight(telegram_id: int, rule_id: str, text: str, tone: str) -> None:
        if Database.pool is None:
            raise RuntimeError("Database pool uninitialized")
            
        async with Database.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO user_insight_history (telegram_id, rule_id, message_text, tone)
                   VALUES ($1, $2, $3, $4)""",
                telegram_id, rule_id, text, tone
            )
