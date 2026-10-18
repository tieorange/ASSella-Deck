"""Exercise the fork installer against fake releases and existing app files."""

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET = "ASSella-Deck.AppImage"
RELEASE_BASE = "https://github.com/tieorange/ASSella-Deck/releases/download/"


class SideBySideInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="assella-deck-install-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.fixture = self.root / "fixture"
        self.bin = self.root / "bin"
        self.fixture.mkdir()
        self.bin.mkdir()
        (self.data / "ACCELA").mkdir(parents=True)
        (self.data / "ACCELA-Original").mkdir()
        (self.data / "applications").mkdir()
        icon_dir = self.data / "icons/hicolor/256x256/apps"
        icon_dir.mkdir(parents=True)
        self.legacy = {
            self.data / "ACCELA/ASSella.AppImage": b"upstream assella\n",
            self.data / "ACCELA/ACCELA.AppImage.bak": b"original accela backup\n",
            self.data / "ACCELA-Original/ACCELA.AppImage": b"original accela\n",
            self.data / "applications/accela.desktop": b"ACCELA desktop\n",
            self.data / "applications/assella.desktop": b"ASSella desktop\n",
            icon_dir / "accela.png": b"ACCELA icon\n",
            icon_dir / "assella.png": b"ASSella icon\n",
        }
        for path, contents in self.legacy.items():
            path.write_bytes(contents)
        self.legacy_link = self.data / "ACCELA/ACCELA.AppImage"
        self.legacy_link.symlink_to("ASSella.AppImage")

        curl = self.bin / "curl"
        curl.write_text(
            "#!/usr/bin/env python3\n"
            "import os, pathlib, shutil, sys\n"
            "args = sys.argv[1:]\n"
            "url = next(a for a in args if a.startswith('https://'))\n"
            "base = pathlib.Path(os.environ['ASSDECK_TEST_FIXTURE'])\n"
            "if url.endswith('/releases'): source = base / 'releases.json'\n"
            "elif url.endswith('.sha256'): source = base / 'checksum.txt'\n"
            "elif url.endswith('.AppImage'): source = base / 'AppImage'\n"
            "elif url.endswith('icon.png'): source = base / 'icon.png'\n"
            "else: sys.exit(22)\n"
            "if not source.exists(): sys.exit(22)\n"
            "if '-o' in args: shutil.copyfile(source, args[args.index('-o') + 1])\n"
            "else: sys.stdout.buffer.write(source.read_bytes())\n"
        )
        curl.chmod(0o755)
        (self.fixture / "icon.png").write_bytes(b"fork icon\n")
        self.env = dict(os.environ)
        self.env.update({
            "XDG_DATA_HOME": str(self.data),
            "ASSDECK_TEST_FIXTURE": str(self.fixture),
            "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
        })

    def release(self, tag: str, contents: bytes, bad_checksum=False):
        (self.fixture / "AppImage").write_bytes(contents)
        digest = hashlib.sha256(contents).hexdigest()
        if bad_checksum:
            digest = "0" * 64
        (self.fixture / "checksum.txt").write_text(f"{digest}  {ASSET}\n")
        assets = [
            {"name": name, "browser_download_url": RELEASE_BASE + tag + "/" + name}
            for name in (ASSET, ASSET + ".sha256")
        ]
        (self.fixture / "releases.json").write_text(
            json.dumps([{"tag_name": tag, "assets": assets}])
        )

    def run_installer(self, *args, success=True):
        result = subprocess.run(
            ["bash", str(ROOT / "install.sh"), *args],
            env=self.env, text=True, capture_output=True,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        self.assert_legacy_unchanged()
        return result

    def assert_legacy_unchanged(self):
        for path, contents in self.legacy.items():
            self.assertEqual(path.read_bytes(), contents, str(path))
        self.assertTrue(self.legacy_link.is_symlink())
        self.assertEqual(self.legacy_link.readlink(), Path("ASSella.AppImage"))

    def test_install_upgrade_rollback_uninstall(self):
        self.release("v3.0.0-beta.1", b"fork first\n")
        self.run_installer("--install")
        fork = self.data / "ASSella-Deck"
        self.assertEqual((fork / ASSET).read_bytes(), b"fork first\n")
        self.assertIn("Name=ASSella Deck", (self.data / "applications/assella-deck.desktop").read_text())
        self.run_installer("--install")
        self.assertEqual((fork / ASSET).read_bytes(), b"fork first\n")
        (fork / "user-data.json").write_text("keep")

        self.release("v3.0.0-beta.2", b"fork second\n")
        self.run_installer("--update")
        self.assertEqual((fork / ASSET).read_bytes(), b"fork second\n")
        self.assertEqual((fork / (ASSET + ".previous")).read_bytes(), b"fork first\n")
        self.run_installer("--rollback")
        self.assertEqual((fork / ASSET).read_bytes(), b"fork first\n")

        self.run_installer("--uninstall")
        self.assertFalse((fork / ASSET).exists())
        self.assertFalse((self.data / "applications/assella-deck.desktop").exists())
        self.assertEqual((fork / "user-data.json").read_text(), "keep")

    def test_missing_or_bad_release_never_replaces_installed_fork(self):
        self.release("v3.0.0-beta.1", b"working fork\n")
        self.run_installer("--install")
        fork_image = self.data / "ASSella-Deck" / ASSET
        self.release("v3.0.0-beta.2", b"bad fork\n", bad_checksum=True)
        self.run_installer("--update", success=False)
        self.assertEqual(fork_image.read_bytes(), b"working fork\n")
        (self.fixture / "releases.json").write_text("[]")
        self.run_installer("--update", success=False)
        self.assertEqual(fork_image.read_bytes(), b"working fork\n")
        (self.fixture / "releases.json").unlink()
        self.run_installer("--update", success=False)
        self.assertEqual(fork_image.read_bytes(), b"working fork\n")

    def test_symlinked_install_directory_is_refused(self):
        (self.data / "ASSella-Deck").symlink_to(self.data / "ACCELA", target_is_directory=True)
        self.release("v3.0.0-beta.1", b"fork\n")
        self.run_installer("--install", success=False)

    def test_symlinked_owned_launcher_icon_and_version_are_refused(self):
        self.release("v3.0.0-beta.1", b"fork\n")
        fork = self.data / "ASSella-Deck"
        fork.mkdir()
        targets = (
            (self.data / "applications/assella-deck.desktop", self.data / "applications/assella.desktop"),
            (self.data / "icons/hicolor/256x256/apps/assella-deck.png", self.data / "icons/hicolor/256x256/apps/assella.png"),
            (fork / "version", self.data / "ACCELA/ASSella.AppImage"),
        )
        for owned, legacy in targets:
            with self.subTest(path=owned):
                owned.symlink_to(legacy)
                self.run_installer("--install", success=False)
                self.assertTrue(owned.is_symlink())
                owned.unlink()

    def test_data_root_inside_accela_is_refused(self):
        self.release("v3.0.0-beta.1", b"fork\n")
        self.env["XDG_DATA_HOME"] = str(self.data / "ACCELA")
        self.run_installer("--install", success=False)
        self.assertFalse((self.data / "ACCELA/ASSella-Deck").exists())

    def test_upstream_or_stable_release_is_not_installed(self):
        self.release("v3.0.0-beta.1", b"not the fork\n")
        releases = json.loads((self.fixture / "releases.json").read_text())
        for asset in releases[0]["assets"]:
            asset["browser_download_url"] = asset["browser_download_url"].replace(
                "tieorange/ASSella-Deck", "niwia/ASSella"
            )
        (self.fixture / "releases.json").write_text(json.dumps(releases))
        self.run_installer("--install", success=False)
        self.assertFalse((self.data / "ASSella-Deck" / ASSET).exists())

        self.release("v3.0.0", b"stable fork\n")
        self.run_installer("--install", success=False)
        self.assertFalse((self.data / "ASSella-Deck" / ASSET).exists())


if __name__ == "__main__":
    unittest.main()
