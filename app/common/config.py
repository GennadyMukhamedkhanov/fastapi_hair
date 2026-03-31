import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"