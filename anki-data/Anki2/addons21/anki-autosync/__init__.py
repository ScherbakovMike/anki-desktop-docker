# anki-autosync — headless AnkiWeb login + automatic sync.
#
# For running Anki in a container with no GUI user. Reads credentials from env
# vars (typically a Kubernetes Secret) and uses Anki's own mw.pm / mw.col APIs,
# so it stays compatible across versions:
#
#   ANKI_USERNAME            AnkiWeb email / account id
#   ANKI_PASSWORD            AnkiWeb password
#   ANKI_SYNC_INTERVAL       seconds between syncs (default 300, 0 disables)
#   ANKI_FULL_SYNC_DIRECTION ambiguous full-sync direction: download (default) / upload

from __future__ import annotations

import os

from aqt import gui_hooks, mw
from aqt.qt import QTimer

ADDON = "anki-autosync"

# Guards against overlapping sync runs (initial sync, timer tick, close).
_syncing = False
_timer: QTimer | None = None


def _log(msg: str) -> None:
    print(f"[{ADDON}] {msg}", flush=True)


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _full_sync_upload_default() -> bool:
    return _env("ANKI_FULL_SYNC_DIRECTION", "download").lower() == "upload"


# --- sync ------------------------------------------------------------------


def _finish() -> None:
    global _syncing
    _syncing = False


def _start_sync() -> None:
    """Run a normal sync in the background; escalate to a full sync if needed."""
    global _syncing
    if _syncing:
        return
    auth = mw.pm.sync_auth()
    if not auth:
        _log("no sync auth configured; skipping sync")
        return
    _syncing = True

    def task():
        return mw.col.sync_collection(auth, mw.pm.media_syncing_enabled())

    mw.taskman.run_in_background(task, _on_normal_sync_done)


def _on_normal_sync_done(fut) -> None:
    try:
        out = fut.result()
    except Exception as err:  # noqa: BLE001 - log and recover, never crash Anki
        _log(f"sync error: {err}")
        _finish()
        return

    # Persist a redirected endpoint if the server provided one.
    new_endpoint = getattr(out, "new_endpoint", None)
    if new_endpoint:
        setter = getattr(mw.pm, "set_current_sync_url", None)
        if setter:
            setter(new_endpoint)

    if out.required in (out.NO_CHANGES, out.NORMAL_SYNC):
        _log(f"sync complete (required={out.required})")
        _finish()
        return

    # A full sync is required (typical on a fresh container pulling an existing
    # AnkiWeb collection). Pick a direction and run it the way the GUI does.
    if out.required == out.FULL_DOWNLOAD:
        upload = False
    elif out.required == out.FULL_UPLOAD:
        upload = True
    else:  # ambiguous FULL_SYNC conflict
        upload = _full_sync_upload_default()
        _log(
            "ambiguous full-sync conflict; using "
            f"ANKI_FULL_SYNC_DIRECTION={'upload' if upload else 'download'}"
        )

    server_usn = out.server_media_usn if mw.pm.media_syncing_enabled() else None
    _full_sync(upload, server_usn)


def _full_sync(upload: bool, server_usn) -> None:
    direction = "upload" if upload else "download"
    _log(f"full sync required: performing full {direction}")

    gui_hooks.collection_will_temporarily_close(mw.col)
    mw.col.close_for_full_sync()

    def task():
        mw.col.full_upload_or_download(
            auth=mw.pm.sync_auth(), server_usn=server_usn, upload=upload
        )

    def done(fut) -> None:
        mw.reopen(after_full_sync=True)
        mw.reset()
        try:
            fut.result()
            _log(f"full {direction} complete")
        except Exception as err:  # noqa: BLE001
            _log(f"full {direction} error: {err}")
        monitor = getattr(getattr(mw, "media_syncer", None), "start_monitoring", None)
        if monitor:
            monitor()
        _finish()

    mw.taskman.run_in_background(task, done)


# --- login -----------------------------------------------------------------


def _login_then_sync() -> None:
    username = _env("ANKI_USERNAME")
    password = _env("ANKI_PASSWORD")
    if not (username and password):
        _log("ANKI_USERNAME/ANKI_PASSWORD not set; skipping auto-login")
        return
    _log(f"logging in to AnkiWeb as {username}")

    def task():
        return mw.col.sync_login(username, password, mw.pm.sync_endpoint())

    def done(fut) -> None:
        try:
            auth = fut.result()
        except Exception as err:  # noqa: BLE001
            _log(f"login failed: {err}")
            return
        mw.pm.set_sync_key(auth.hkey)
        mw.pm.set_sync_username(username)
        _log("login succeeded; sync auth stored")
        _start_sync()

    mw.taskman.run_in_background(task, done)


# --- lifecycle -------------------------------------------------------------


def _on_profile_open() -> None:
    global _timer

    if mw.pm.sync_auth():
        # Already authenticated (e.g. credentials persisted on the volume).
        _log("existing sync auth found; syncing")
        _start_sync()
    else:
        _login_then_sync()

    interval = int(_env("ANKI_SYNC_INTERVAL", "300") or "0")
    if interval > 0:
        _timer = QTimer(mw)
        _timer.timeout.connect(_start_sync)
        _timer.start(interval * 1000)
        _log(f"automatic sync every {interval}s")


def _on_profile_close() -> None:
    # Best-effort final sync. May not finish before shutdown, but normal syncs
    # are fast; the periodic timer is the primary mechanism.
    if mw.pm.sync_auth():
        _start_sync()


gui_hooks.profile_did_open.append(_on_profile_open)
gui_hooks.profile_will_close.append(_on_profile_close)
