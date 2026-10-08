# Remembers open tabs/windows (and their working directories) between kitty runs.
#
# Every change (new/closed tab or window, focus, title i.e. `cd`) schedules a save of the
# whole kitty state to SESSION_PATH, which kitty.conf loads via `startup_session`.
# The save is delayed, so quitting kitty (which closes everything at once) never
# overwrites the session with an empty one: the pending timer simply never fires.
#
# It also remembers the size of the OS window (not just of the last closed one, which is
# what kitty's own `remember_window_size` does and which stores the maximized size when you
# quit while maximized). Every resize schedules a check; the size is saved to SIZE_PATH
# unless the window looks maximized. Every new OS window is resized to the saved size once.
# Needs `remember_window_size no` in kitty.conf, otherwise kitty applies its own cache first.

import json
import os
from typing import Any

from kitty.boss import Boss
from kitty.config import atomic_save
from kitty.fast_data_types import add_timer, get_os_window_size, glfw_get_monitor_workarea
from kitty.session import parse_save_as_options_spec_args
from kitty.window import Window

SESSION_PATH = os.path.expanduser('~/.local/state/kitty/last-session.kitty-session')
SIZE_PATH = os.path.expanduser(os.environ.get('KITTY_WINDOW_SIZE_FILE', '~/.local/state/kitty/window-size.json'))
DELAY = 2.0
SIZE_DELAY = 1.0  # lets a drag-resize settle before reading the size
MAXIMIZED_RATIO = 0.9  # a window covering >= 90% of a monitor in both axes is treated as maximized (the panel eats ~5% of the height)

# `kitty +open <file/URL>` (kitty-open.desktop) creates a placeholder window running
# `kitty +runpy input()` instead of a shell. Saving it would make every later start restore
# a window where nothing can be typed, so it is left out of the session.
# (Dots instead of `\(\)`: parentheses are grouping in kitty's match syntax.)
SAVE_OPTS = parse_save_as_options_spec_args(['--match=not cmdline:^input..$'])[0]

_pending = False
_size_pending: set[int] = set()
_size_timer = False
_sized: set[int] = set()  # OS windows that already got the saved size applied


def _save(boss: Boss) -> None:
    global _pending
    _pending = False
    session = '\n'.join(boss.serialize_state_as_session(SESSION_PATH, SAVE_OPTS))
    if 'launch' not in session:
        return
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
    atomic_save(session.encode(), SESSION_PATH)


def _schedule(boss: Boss) -> None:
    global _pending
    # Only the main instance (started without --session, e.g. not `kitty --session=none`
    # from the file manager) owns the remembered session.
    if getattr(boss.args, 'session', ''):
        return
    if not _pending:
        _pending = True
        add_timer(lambda _timer_id: _save(boss), DELAY, False)


def _load_size() -> tuple[int, int] | None:
    try:
        with open(SIZE_PATH) as f:
            w, h = json.load(f)['size']
        return int(w), int(h)
    except Exception:
        return None


def _looks_maximized(width: int, height: int) -> bool:
    try:
        for area in glfw_get_monitor_workarea():
            if width >= area[2] * MAXIMIZED_RATIO and height >= area[3] * MAXIMIZED_RATIO:
                return True
    except Exception:
        pass
    return False


def _check_size(boss: Boss) -> None:
    global _size_timer
    _size_timer = False
    pending = _size_pending.copy()
    _size_pending.clear()
    for os_window_id in pending:
        if os_window_id not in boss.os_window_map:
            continue
        metrics = get_os_window_size(os_window_id)
        if metrics is None or metrics['is_layer_shell']:
            continue
        size = (metrics['width'], metrics['height'])
        if _looks_maximized(*size) or size == _load_size():
            continue
        os.makedirs(os.path.dirname(SIZE_PATH), exist_ok=True)
        atomic_save(json.dumps({'size': list(size)}).encode(), SIZE_PATH)


def _schedule_size_check(boss: Boss, window: Window) -> None:
    global _size_timer
    os_window_id = getattr(window, 'os_window_id', None)
    if os_window_id is None:
        return
    _size_pending.add(os_window_id)
    if not _size_timer:
        _size_timer = True
        add_timer(lambda _timer_id: _check_size(boss), SIZE_DELAY, False)


def _apply_saved_size(boss: Boss, window: Window) -> None:
    # `on_resize` does not fire when a window is created, so the first focus/title event of
    # a new OS window is the earliest hook available.
    os_window_id = getattr(window, 'os_window_id', None)
    if os_window_id is None or os_window_id in _sized:
        return
    _sized.add(os_window_id)
    saved = _load_size()
    if saved is None:
        return
    metrics = get_os_window_size(os_window_id)
    if metrics is None or metrics['is_layer_shell']:
        return
    if (metrics['width'], metrics['height']) != saved:
        boss.resize_os_window(os_window_id, saved[0], saved[1], 'pixels', metrics=metrics)


def on_load(boss: Boss, data: dict[str, Any]) -> None:
    _schedule(boss)


def on_focus_change(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    _apply_saved_size(boss, window)
    _schedule(boss)


def on_title_change(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    _apply_saved_size(boss, window)
    _schedule(boss)


def on_resize(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    _schedule_size_check(boss, window)


def on_close(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    _schedule(boss)
