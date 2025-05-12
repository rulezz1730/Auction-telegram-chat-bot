import os
from dotenv import load_dotenv # type: ignore

load_dotenv()

TOKEN = os.getenv("TOKEN")

ADMIN_ID = list(map(int, os.getenv("ADMIN_ID", "").split(",")))


