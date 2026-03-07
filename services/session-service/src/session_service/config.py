import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionSettings:
    database_url: str = "sqlite:///./forza_sessions.db"

    @classmethod
    def from_env(cls) -> "SessionSettings":
        return cls(database_url=os.getenv("SESSION_DATABASE_URL", cls.database_url))
