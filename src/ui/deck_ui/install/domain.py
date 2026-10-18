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

    def review_lines(self) -> tuple[str, ...]:
        return (
            f"Game  ·  {self.game_name} ({self.appid})",
            f"Branch  ·  {self.branch}",
            f"Build  ·  {self.build or 'Latest available'}",
            f"Content  ·  {len(self.depots)} depot(s)",
            f"Storage  ·  {self.storage or 'Choose a storage location'}",
            f"Download  ·  {'Steam client' if self.backend == 'native' else 'ASSella Downloader'}",
        )
