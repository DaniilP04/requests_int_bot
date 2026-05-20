import asyncpg
import os
from typing import Optional
from aiogram import Bot
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.pool.Pool] = None #создается пул соединений

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            database=os.getenv("PGDATABASE"),
            host=os.getenv("PGHOST"),
            port=int(os.getenv("PGPORT", "5432"))
        )

    async def close(self):
        await self.pool.close()

    async def add_request(self, full_name, school, class_name, phone, device_type, telegram_id, source='Телеграм'):
        query = """
                    INSERT INTO requests (full_name, school, class, phone, device_type, source, telegram_id, track_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, generate_track_id())
                    RETURNING track_id, password
                """
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(query, full_name, school, class_name, phone,
                                     device_type, source, telegram_id)
            return result
        
    async def check_by_telegram_id(self, telegram_id: int):
        query = """
                    SELECT device_type, status, track_id, password FROM requests
                    WHERE telegram_id = $1 ORDER BY created_at DESC
                """
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, telegram_id)  

    async def get_schools_by_type(self, school_type: str):
        query = "SELECT id, name FROM schools WHERE type = $1 ORDER BY name"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, school_type)
            return rows

    async def get_school_by_id(self, school_id: int):
        query = "SELECT id, name FROM schools WHERE id = $1"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, school_id)
            return row
        
    async def is_duplicate_request(self, full_name, school, class_name, device_type):
        query = """
                    SELECT id FROM requests
                    WHERE full_name = $1 AND school = $2 AND class = $3 AND device_type = $4
                """

        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(query, full_name, school, class_name, device_type)
            return result is not None
        
    async def get_active_products(self):
        query = """
            SELECT code, name, price
            FROM products
            WHERE is_active = true
            ORDER BY id
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return rows


     
db = Database()
