from dataclasses import dataclass, field


@dataclass
class InstallDraft:
    game_name: str = ""
    appid: str = ""
    package_path: str = ""
    branch: str = "public"
    build: str = ""
    depots: list[str] = field(default_factory=list)
    storage: str = ""
    backend: str = "assella"
    metadata: dict = field(default_factory=dict)

    def review_items(self, storage_label: str = "") -> tuple[tuple[str, str], ...]:
        return (
            ("Game", f"{self.game_name} · {self.appid}"),
            ("Branch", self.branch),
            ("Build", self.build or "Latest available"),
            ("Content", f"{len(self.depots)} selected depot{'s' if len(self.depots) != 1 else ''}"),
            ("Storage", storage_label or self.storage or "Choose a storage location"),
            ("Download", "Steam client" if self.backend == "native" else "ASSella Downloader"),
        )

    def review_lines(self) -> tuple[str, ...]:
        return tuple(f"{key}  ·  {value}" for key, value in self.review_items())
