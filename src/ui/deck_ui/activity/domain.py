from dataclasses import dataclass


@dataclass(frozen=True)
class ActivitySnapshot:
    active_name: str = "No active work"
    active_status: str = "Your queue is clear."
    progress: int = 0
    progress_known: bool = False
    is_active: bool = False
    can_pause: bool = False
    is_paused: bool = False
    queued: tuple[str, ...] = ()
    failure: str = ""
    can_retry: bool = False
