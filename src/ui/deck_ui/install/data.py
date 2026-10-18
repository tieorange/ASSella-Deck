"""Map the selection dialog into the existing queue metadata contract."""

import json

from .domain import InstallDraft


def draft_from_selection(parsed_data, package_path, branch, metadata, selector) -> InstallDraft:
    depots = selector.get_selected_depots()
    if not depots:
        raise ValueError("Choose at least one depot.")
    storage = selector.get_selected_storage() or metadata.get("library_path", "")
    if not storage:
        raise ValueError("Choose a storage location.")
    appid = str(parsed_data.get("appid", ""))
    selected_branch = selector.get_selected_branch() if hasattr(selector, "get_selected_branch") else branch
    selected_branch = selected_branch or branch
    merged = dict(metadata)
    merged.update({
        "appid": appid,
        "app_id": appid,
        "game_name": parsed_data.get("game_name", f"App {appid}"),
        "branch": selected_branch,
        "selected_depots_list": depots,
        "library_path": storage,
        "download_backend": "assella",
    })
    build = ""
    if hasattr(selector, "is_build_pinned") and selector.is_build_pinned():
        build = selector.get_selected_build() or ""
        merged.update({"pin_build": True, "pinned_build_id": build, "buildid": build, "is_rollback": True})
    if hasattr(selector, "get_manifest_overrides"):
        overrides = selector.get_manifest_overrides()
        if overrides:
            merged["manifest_overrides"] = overrides
    return InstallDraft(
        game_name=merged["game_name"], appid=appid, package_path=str(package_path),
        branch=selected_branch, build=build, depots=depots, storage=storage,
        metadata=merged,
    )


def persist_draft(settings, draft: InstallDraft, parsed_data: dict):
    settings.setValue(f"selected_branch/{draft.appid}", draft.branch)
    settings.setValue(
        f"depot_selection/{draft.appid}",
        json.dumps({
            "selected": draft.depots,
            "all_available": list(parsed_data.get("depots", {})),
            "descriptions": {
                depot: parsed_data.get("depots", {}).get(depot, {}).get("desc", "")
                for depot in draft.depots
            },
        }),
    )
    if draft.build:
        settings.setValue(f"pin_build/{draft.appid}", True)
