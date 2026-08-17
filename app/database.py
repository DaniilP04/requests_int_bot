import asyncpg
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


ACTIVE_DUPLICATE_STATUSES = ("Принято", "В обработке", "Готово к выдаче")


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.pool.Pool] = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            database=os.getenv("PGDATABASE"),
            host=os.getenv("PGHOST"),
            port=int(os.getenv("PGPORT", "5432"))
        )

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def add_request(self, full_name, school, class_name, phone, device_type, telegram_id, source='Телеграм'):
        query = """
            INSERT INTO requests (full_name, school, "class", phone, device_type, source, telegram_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING track_id, password
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                query,
                full_name,
                school,
                class_name,
                phone,
                device_type,
                source,
                telegram_id
            )

    async def check_by_telegram_id(self, telegram_id: int):
        query = """
            SELECT device_type, status, track_id, password
            FROM requests
            WHERE telegram_id = $1
            ORDER BY created_at DESC
        """
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, telegram_id)

    async def get_schools_by_type(self, school_type: str):
        query = """
            SELECT id, name
            FROM schools
            WHERE type = $1
            ORDER BY name
        """
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, school_type)

    async def get_school_by_id(self, school_id: int):
        query = """
            SELECT id, name
            FROM schools
            WHERE id = $1
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, school_id)

    async def is_duplicate_request(self, full_name, school, class_name):
        query = """
            SELECT id
            FROM requests
            WHERE deleted = false
              AND lower(full_name) = lower($1)
              AND lower(school) = lower($2)
              AND lower("class") = lower($3)
              AND status = ANY($4::text[])
            LIMIT 1
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                full_name.strip(),
                school.strip(),
                class_name.strip(),
                list(ACTIVE_DUPLICATE_STATUSES)
            )
            return row is not None

    async def get_public_products(self):
        query = """
            SELECT code, name, color, price, quantity
            FROM products
            WHERE is_active = true
            ORDER BY id
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)

        grouped = {}

        for row in rows:
            name = (row["name"] or "").strip()
            color = (row["color"] or "").strip()
            price = row["price"]
            quantity = row["quantity"]

            if name == "Браслет" and not color:
                continue

            if name == "Браслет" and color and quantity <= 0:
                continue

            if name not in grouped:
                grouped[name] = {
                    "code": row["code"],
                    "name": name,
                    "price": price,
                    "colors": []
                }

            if color and color not in grouped[name]["colors"]:
                grouped[name]["colors"].append(color)

        products = list(grouped.values())
        for product in products:
            product["colors"].sort()

        return products


db = Database()