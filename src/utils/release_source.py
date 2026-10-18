"""Release source for this Steam Deck fork.

Keep these identifiers separate from upstream so merges cannot redirect updates.
"""

RELEASE_REPOSITORY = "tieorange/ASSella-Deck"
RELEASE_BRANCH = "deck/beta"


def releases_api_url() -> str:
    return f"https://api.github.com/repos/{RELEASE_REPOSITORY}/releases"


def version_url() -> str:
    return f"https://raw.githubusercontent.com/{RELEASE_REPOSITORY}/{RELEASE_BRANCH}/src/res/version"
