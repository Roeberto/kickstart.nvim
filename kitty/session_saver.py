# Remembers open tabs/windows (and their working directories) between kitty runs.
#
# Every change (new/closed tab or window, focus, title i.e. `cd`) schedules a save of the
# whole kitty state to SESSION_PATH, which kitty.conf loads via `startup_session`.
# The save is delayed, so quitting kitty (which closes everything at once) never
# overwrites the session with an empty one: the pending timer simply never fires.

import os
from typing import Any

from kitty.boss import Boss
from kitty.config import atomic_save
from kitty.fast_data_types import add_timer
from kitty.window import Window

SESSION_PATH = os.path.expanduser('~/.local/state/kitty/last-session.kitty-session')
DELAY = 2.0

_pending = False


def _save(boss: Boss) -> None:
    global _pending
    _pending = False
    session = '\n'.join(boss.serialize_state_as_session(SESSION_PATH))
    if 'launch' not in session:
        return
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
    atomic_save(session.encode(), SESSION_PATH)


def _schedule(boss: Boss) -> None:
    global _pending
    if not _pending:
        _pending = True
        add_timer(lambda _timer_id: _save(boss), DELAY, False)


def on_load(boss: Boss, data: dict[str, Any]) -> None:
    _schedule(boss)


def on_focus_change(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    _schedule(boss)


def on_title_change(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    _schedule(boss)


def on_close(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    _schedule(boss)
