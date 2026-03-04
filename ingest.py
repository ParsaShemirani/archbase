import shutil
from hashlib import file_digest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing_extensions import Annotated

from sqlalchemy import select
from sqlalchemy.orm import Session as SessionType
import typer

from env_vars import TERMINAL_PATH, STORAGE_PATH, PENDING_STORAGE_PATH
from connection import Session
from models import File, Bundle, FileBundle

ISO_FMT_Z = "%Y-%m-%dT%H:%M:%S%z"


def generate_sha256_hash(file_path: Path) -> str:
    with file_path.open("rb") as f:
        return file_digest(f, "sha256").hexdigest()


def get_sorted_files(dir_path: Path) -> list[Path] | None:
    file_paths = sorted(
        [f for f in dir_path.iterdir() if not f.name.startswith(".") and f.is_file()]
    )
    if file_paths:
        return file_paths
    else:
        return None

def get_sorted_directories(dir_path: Path) -> list[Path] | None:
    directory_paths = sorted(
        [d for d in dir_path.iterdir() if not d.name.startswith(".") and d.is_dir()]
    )
    if directory_paths:
        return directory_paths
    else:
        return None


def get_existing_file(file: File, session: SessionType) -> File | None:
    existing_file = session.scalar(
        select(File).where(File.sha256_hash == file.sha256_hash)
    )
    if existing_file:
        return existing_file
    else:
        return None


def determine_created_time(file_path: Path) -> datetime:
    # Very specific to MacOS file system
    file_stats = file_path.stat()
    modified_timestamp = file_stats.st_mtime
    birth_timestamp = file_stats.st_birthtime

    if modified_timestamp > birth_timestamp:
        created_timestamp = birth_timestamp
    else:
        created_timestamp = modified_timestamp

    return datetime.fromtimestamp(timestamp=created_timestamp, tz=timezone.utc)

def create_file(file_path: Path) -> File:
    file = File(
        name=file_path.name,
        extension=file_path.suffix.lstrip(".").lower(),
        sha256_hash=generate_sha256_hash(file_path),
        size=file_path.stat().st_size,
        created_ts=determine_created_time(file_path).strftime(format=ISO_FMT_Z),
        created_ts_percision=None,
        description=None
    )

    return file

def bundler(path: Path, percision: int, session: SessionType, parent_id: int | None = None) -> None:
    bundle = Bundle(
        name=path.name,
        parent_id=parent_id,
        description=None
    )
    session.add(bundle)
    session.flush()

    for child in path.iterdir():
        if child.is_dir():
            bundler(path=child, session=session, parent_id=bundle.id)
        else:
            if not child.name.startswith("."):
                file = create_file(file_path=child)
                file.created_ts_percision = percision
                existing_file = get_existing_file(file=file, session=session)
                if existing_file:
                    file = existing_file
                else:
                    session.add(file)
                    session.flush()

                    pending_path = PENDING_STORAGE_PATH / file.sha256_hash
                    #child.rename(pending_path)
                    shutil.copy2(str(child), str(pending_path))

                file_bundle = FileBundle(
                    file_id=file.id,
                    bundle_id=bundle.id
                )
                session.add(file_bundle)


def storer(session: SessionType):
    all_pending_files = get_sorted_files(dir_path=PENDING_STORAGE_PATH)

    for f in all_pending_files:
        existing_file = session.scalar(select(File).where(File.sha256_hash == f.name))
        if not existing_file:
            raise FileNotFoundError("File not found in database")
        shutil.copy2(str(f), str(STORAGE_PATH / f.name))

def main(
        file: Annotated[bool, typer.Option("--file", "-f")] = False,
        bundle: Annotated[bool, typer.Option("--bundle", "-b")] = False,
        percision: Annotated[int, typer.Option("--percision", "-p")] = None,
        store: Annotated[bool, typer.Option("--store", "-s")] = False
):
    if bundle:
        if percision is None:
            raise ValueError("Precision must be set for created_ts")
        
        directories = get_sorted_directories(dir_path=TERMINAL_PATH)
        if directories is None:
            raise ValueError("No directories found in terminal")
        with Session() as session:
            with session.begin():
                bundler(path=directories[0], percision=percision, session=session)
    elif file:
        if percision is None:
            raise ValueError("Precision must be set for created_ts")
        
        files = get_sorted_files(dir_path=TERMINAL_PATH)
        if files is None:
            raise ValueError("No files found in terminal")
        with Session() as session:
            with session.begin():
                for fp in files:
                    f = create_file(file_path=fp)
                    f.created_ts_percision = percision
                    session.add(f)
                    pending_path = PENDING_STORAGE_PATH / f.sha256_hash
                    fp.rename(pending_path)
                session.flush()
    elif store:
        with Session() as session:
            storer(session=session)

if __name__ == "__main__":
    typer.run(main)
