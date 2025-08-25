import os


def extract_direct_database_url() -> str:
    return os.environ["DATABASE_URL"].replace("+asyncpg", "")
