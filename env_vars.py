import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

STR_DATA_DIRECTORY = os.getenv("DATA_DIRECTORY_PATH")
if not STR_DATA_DIRECTORY:
    raise RuntimeError("DATA_DIRECTORY_PATH not set in .env")
DATA_DIRECTORY_PATH = Path(STR_DATA_DIRECTORY)
TERMINAL_PATH = DATA_DIRECTORY_PATH / "terminal"
PENDING_STORAGE_PATH = DATA_DIRECTORY_PATH / "pending_storage"
EMBEDDINGS_PATH = DATA_DIRECTORY_PATH / "embeddings"

DATABASE_PATH = DATA_DIRECTORY_PATH / "filebase.db"


STR_STORAGE_DIRECTORY = os.getenv("STORAGE_DIRECTORY_PATH")
if not STR_STORAGE_DIRECTORY:
    raise RuntimeError("STORAGE_DIRECTORY_PATH not set in .env")

STORAGE_PATH = Path(STR_STORAGE_DIRECTORY)  

if __name__ == "__main__":
    for path in (DATA_DIRECTORY_PATH, TERMINAL_PATH, PENDING_STORAGE_PATH, EMBEDDINGS_PATH, STORAGE_PATH):
        path.mkdir(parents=True, exist_ok=True)
