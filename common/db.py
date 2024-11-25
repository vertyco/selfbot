from __future__ import annotations

import os
import sys
import typing as t
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel

IS_EXE = True if (getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")) else False
if IS_EXE:
    ROOT_DIR = Path(os.path.dirname(os.path.abspath(sys.executable)))
else:
    ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent

DB_PATH = ROOT_DIR / "db.json"


class Base(BaseModel):
    @classmethod
    def load(cls) -> t.Slef:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        if DB_PATH.exists():
            return cls.model_validate_json(DB_PATH.read_text())
        return cls()

    def save(self) -> None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        dump = self.model_dump_json(indent=4)
        tmp_path = DB_PATH.parent / f"{DB_PATH.stem}-{uuid4().fields[0]}.tmp"
        with tmp_path.open(encoding="utf-8", mode="w") as fs:
            fs.write(dump)
            fs.flush()
            os.fsync(fs.fileno())

        tmp_path.replace(DB_PATH)

        if hasattr(os, "O_DIRECTORY"):
            fd = os.open(DB_PATH.parent, os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)


class DB(Base):
    # {channel_id: datetime}
    sent_messages: dict[int, datetime] = {}
