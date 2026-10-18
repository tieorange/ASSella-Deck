"""Read-only bridge from existing managers to the Activity view model."""

from pathlib import Path

from .domain import ActivitySnapshot


def snapshot_from_main_window(main_window) -> ActivitySnapshot:
    task = getattr(main_window, "task_manager", None)
    queue = getattr(main_window, "job_queue", None)
    progress = getattr(main_window, "progress_bar", None)
    active = bool(task and task.is_processing)
    metadata = (getattr(task, "current_job_metadata", None) or {}) if task else {}
    name = metadata.get("game_name") or (Path(str(task.current_job)).name if active and task.current_job else "Working")
    queued = tuple(
        job.get("metadata", {}).get("game_name")
        or job.get("workshop_data", {}).get("display_name")
        or Path(str(job.get("path", "Queued job"))).name
        for job in (getattr(queue, "job_queue", []) or [])
    )
    failed = getattr(task, "last_failed_job", None) if task else None
    progress_known = bool(progress and progress.maximum() > progress.minimum())
    return ActivitySnapshot(
        active_name=name if active else "No active work",
        active_status="Paused" if active and task.is_download_paused else "In progress" if active else "Your queue is clear." if not queued else "Next job will start automatically.",
        progress=progress.value() if progress_known else 0,
        progress_known=progress_known,
        is_active=active,
        can_pause=bool(active and getattr(task, "download_task", None)),
        is_paused=bool(active and task.is_download_paused),
        queued=queued,
        failure=str(failed.get("error", "")) if failed else "",
        can_retry=bool(failed and Path(str(failed.get("path", ""))).is_file()),
    )
