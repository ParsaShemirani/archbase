from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    ForeignKey,
    Integer,
    TEXT,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    MappedAsDataclass,
    Mapped,
    mapped_column,
)

ISO_FMT_Z = "%Y-%m-%dT%H:%M:%S%z"


def get_current_time_str() -> str:
    now = datetime.now(tz=timezone.utc)
    now_str = now.strftime(format=ISO_FMT_Z)
    return now_str


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    # Name is original pathlib.Path.name value including extension
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    extension: Mapped[str] = mapped_column(TEXT, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(TEXT, nullable=False, unique=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_ts: Mapped[str] = mapped_column(TEXT, nullable=False)
    description: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    inserted_ts: Mapped[str] = mapped_column(
        TEXT, nullable=False, default_factory=get_current_time_str, init=False
    )

class Bundle(Base):
    __tablename__ = "bundles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(TEXT, nullable=False)

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("bundles.id"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    inserted_ts: Mapped[str] = mapped_column(
        TEXT, nullable=False, default_factory=get_current_time_str, init=False
    )

class FileBundle(Base):
    __tablename__ = "file_bundles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"))
    bundle_id: Mapped[int] = mapped_column(ForeignKey("bundles.id"))

    inserted_ts: Mapped[str] = mapped_column(
        TEXT, nullable=False, default_factory=get_current_time_str, init=False
    )

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    description: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    inserted_ts: Mapped[str] = mapped_column(
        TEXT, nullable=False, default_factory=get_current_time_str, init=False
    )

class FileTag(Base):
    __tablename__ = "file_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"))
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))
    
    inserted_ts: Mapped[str] = mapped_column(
        TEXT, nullable=False, default_factory=get_current_time_str, init=False
    )
