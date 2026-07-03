import os

from app.postgres_db_provider import PostgresDBProvider

DATABASE_URL = os.environ["DATABASE_URL"]
DATABASE = PostgresDBProvider(DATABASE_URL)
