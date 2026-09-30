"""One environment configuration contract for installer and server."""
from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    mode: str = "portal"
    state_dir: Path = Path(".local/framework")
    secure_cookies: bool = False
    session_hours: int = 8

    def __post_init__(self):
        if self.mode not in {"portal", "framework"}:
            raise ValueError("AMP_MODE must be portal or framework")
        if not 1 <= self.session_hours <= 24:
            raise ValueError("AMP_SESSION_HOURS must be between 1 and 24")
        resolved = Path(self.state_dir).resolve()
        protected = (Path("C:/Users/mbeni/Downloads/datasets/_imports").resolve(),
                     Path("C:/Users/mbeni/Downloads/datasets/_exports").resolve())
        if any(resolved == p or p in resolved.parents for p in protected):
            raise ValueError("State directory cannot use protected active acquisition paths")
        object.__setattr__(self, "state_dir", resolved)

    @classmethod
    def from_env(cls):
        secure = os.getenv("AMP_SECURE_COOKIES", "false").lower()
        if secure not in {"true", "false"}:
            raise ValueError("AMP_SECURE_COOKIES must be true or false")
        return cls(mode=os.getenv("AMP_MODE", "portal"),
                   state_dir=Path(os.getenv("AMP_STATE_DIR", ".local/framework")),
                   secure_cookies=secure == "true",
                   session_hours=int(os.getenv("AMP_SESSION_HOURS", "8")))
