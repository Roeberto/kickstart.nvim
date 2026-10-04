# Nautilus extension: "Otwórz w terminalu (kitty)" in the folder and background context menus.
# Needs the nautilus-python package; installed by symlinking this file into
# ~/.local/share/nautilus-python/extensions/.

import subprocess

from gi.repository import GObject, Nautilus

LABEL = 'Otwórz w terminalu (kitty)'


def _open(_item, file):
    path = file.get_location().get_path()
    if path:
        # --session=none: a fresh window in this folder, without the remembered tabs
        subprocess.Popen(['kitty', '--session=none', '--directory', path], start_new_session=True)


class OpenInKitty(GObject.GObject, Nautilus.MenuProvider):
    def get_file_items(self, files):
        if len(files) != 1 or not files[0].is_directory():
            return []
        item = Nautilus.MenuItem(name='OpenInKitty::folder', label=LABEL)
        item.connect('activate', _open, files[0])
        return [item]

    def get_background_items(self, folder):
        item = Nautilus.MenuItem(name='OpenInKitty::background', label=LABEL)
        item.connect('activate', _open, folder)
        return [item]
