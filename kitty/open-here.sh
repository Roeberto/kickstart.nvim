#!/bin/sh
# Launcher for kitty.desktop (Dolphin "Open Terminal Here", file managers, app menu).
#
# File managers start the terminal for a folder either as `kitty --working-directory <folder>`
# or (KDE) only with <folder> as the working directory of the process. kitty.conf has
# `startup_session`, which restores the remembered tabs and ignores that folder, so:
#   1. if a kitty is already running (socket from `listen_on` in kitty.conf), open a new
#      tab in that folder there, preferring the instance whose OS window has focus;
#   2. otherwise start kitty normally (it restores the remembered tabs) and add one more
#      tab in the folder once its socket is up.
# Without a folder (app menu, `kitty` from a shell) kitty behaves as usual.

dir=
prev=
for arg in "$@"; do
    case "$prev" in
        --working-directory|--directory|-d) dir=$arg ;;
    esac
    case "$arg" in
        --working-directory=*|--directory=*) dir=${arg#*=} ;;
    esac
    prev=$arg
done

# Some launchers (e.g. KDE via kitty.desktop) pass the folder only as the working directory
# of the process, not as an argument. $HOME and / are what the app menu / bare launches give.
if [ -z "$dir" ] && [ "$PWD" != "$HOME" ] && [ "$PWD" != / ]; then
    dir=$PWD
fi

if [ -z "$dir" ]; then
    exec kitty "$@"
fi

runtime=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
focused=
any=
for sock in "$runtime"/kitty-*; do
    [ -S "$sock" ] || continue
    windows=$(kitten @ --to "unix:$sock" ls 2>/dev/null) || continue
    [ -n "$any" ] || any=$sock
    case "$windows" in
        *'"is_focused": true'*) focused=$sock ;;
    esac
done

target=${focused:-$any}
if [ -n "$target" ] && kitten @ --to "unix:$target" launch --type=tab --cwd "$dir" >/dev/null 2>&1; then
    exit 0
fi

# No running kitty: start it (restores the remembered tabs), then add the folder as a tab.
# The script waits for kitty to exit so a launcher that kills the process group on exit
# (systemd app scopes) does not take the terminal down with it.
kitty "$@" &
pid=$!
sock=$runtime/kitty-$pid
tries=0
while [ "$tries" -lt 100 ] && kill -0 "$pid" 2>/dev/null; do
    if [ -S "$sock" ] && kitten @ --to "unix:$sock" launch --type=tab --cwd "$dir" >/dev/null 2>&1; then
        break
    fi
    tries=$((tries + 1))
    sleep 0.2
done
wait "$pid"
