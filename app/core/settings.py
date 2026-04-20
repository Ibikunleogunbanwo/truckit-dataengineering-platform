import os

from dotenv import load_dotenv


load_dotenv()


def get_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_int_env(name: str) -> int:
    return int(get_env(name))


def get_float_env(name: str) -> float:
    return float(get_env(name))
