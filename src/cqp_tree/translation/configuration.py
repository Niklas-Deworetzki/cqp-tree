from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Configuration:
    translator: Optional[str] = None
    span: Optional[str] = None
