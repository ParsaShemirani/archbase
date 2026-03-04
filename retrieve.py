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

def retrieve_bundle(bundle_id: int, destination_path: Path, session: SessionType) -> None:
    root_bundle = session.get(Bundle, bundle_id)
    if root_bundle is None:
        raise ValueError("Bundle does not exist")
    
    def _recurse(bundle: Bundle, parent_path: Path) -> None:
        current_path = parent_path / bundle.name
        current_path.mkdir(exist_ok=True)

        files_stmt = (select(File).join(FileBundle, File.id == FileBundle.file_id).where(FileBundle.bundle_id == bundle.id))
        files = session.scalars(files_stmt).all()

        for f in files:
            source_path = STORAGE_PATH / f.sha256_hash
            if not source_path.exists():
                raise FileNotFoundError("Stored file missing")
            target_path = current_path / f.name

            shutil.copy2(source_path, target_path)
        
        child_stmt = select(Bundle).where(Bundle.parent_id == bundle.id)
        children = session.scalars(child_stmt).all()

        for c in children:
            _recurse(bundle=c, parent_path=current_path)
    
    _recurse(root_bundle, destination_path)

def main(
        file_id: Annotated[int, typer.Option("--file_id", "-fid")] = None,
        bundle_id: Annotated[int, typer.Option("--bundle", "-bid")] = None,
):
    if bundle_id:
        with Session() as session:
            retrieve_bundle(bundle_id=bundle_id, destination_path=TERMINAL_PATH, session=session)
    if file_id:
        with Session() as session:
            f = session.scalar(select(File).where(File.id == file_id))
            if f is None:
                raise FileNotFoundError("File id not found in database")
            shutil.copy2(str(STORAGE_PATH / f.sha256_hash), str(TERMINAL_PATH / f.name))
if __name__ == "__main__":
    typer.run(main)