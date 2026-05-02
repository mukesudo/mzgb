from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class LogLine:
    raw: str
    level: Optional[str] = None
    timestamp: Optional[datetime] = None
    message: Optional[str] = None
    extras: dict = field(default_factory=dict)
