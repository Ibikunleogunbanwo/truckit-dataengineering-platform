import psycopg2

from app.core.settings import get_env, get_int_env


def get_db():
    return psycopg2.connect(
        host=get_env("DB_HOST"),
        port=get_int_env("DB_PORT"),
        dbname=get_env("DB_NAME"),
        user=get_env("DB_USER"),
        password=get_env("DB_PASSWORD")
    )
