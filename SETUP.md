# Instalacja konfiguracji na nowym urządzeniu

Konfiguracja Neovima (kickstart.nvim) + kitty + motyw bamboo + Roslyn (C# / Godot).
Testowane na Fedorze (`dnf`); na innych dystrybucjach zmień tylko menedżer pakietów.

## 1. Narzędzia

```bash
sudo dnf install neovim git make unzip ripgrep fd-find tree-sitter-cli kitty wl-clipboard
sudo dnf install dotnet-sdk-10.0
```

- Neovim musi być w wersji **0.12 lub nowszej** (`nvim --version`).
- **.NET SDK 10 jest wymagany** przez Roslyn. Na samym .NET 9 serwer się nie uruchomi
  (`You must install or update .NET to run this application`). Godot i `dotnet build`
  projektu działają obok SDK 10 bez zmian.
- Jeśli `dotnet-sdk-10.0` nie ma w repozytoriach, pobierz SDK z https://dotnet.microsoft.com/download.

## 2. Klucz SSH do GitHuba

Repozytorium jest pobierane przez SSH. Jeśli maszyna nie ma jeszcze klucza:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/Klucz_PC_Robert
cat ~/.ssh/Klucz_PC_Robert.pub        # wklej na GitHub: Settings -> SSH and GPG keys
```

Wpis w `~/.ssh/config`:

```
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/Klucz_PC_Robert
```

Sprawdź: `ssh -T git@github.com` powinno odpowiedzieć `Hi Roeberto!`.
Klucza prywatnego **nie** wkładaj do repozytorium ani nie przesyłaj przez GitHub.
Bez SSH można sklonować przez HTTPS: `https://github.com/Roeberto/kickstart.nvim.git`.

## 3. Pobranie konfiguracji

```bash
# jeśli ~/.config/nvim już istnieje, zrób kopię: mv ~/.config/nvim ~/.config/nvim.bak
git clone git@github.com:Roeberto/kickstart.nvim.git ~/.config/nvim
```

Jeśli katalog już jest (np. z wcześniejszej instalacji): `cd ~/.config/nvim && git pull --rebase origin master`.

## 4. Kitty: symlink katalogu

Kitty szuka `include themes/bamboo.conf` względem `~/.config/kitty/`, a nie względem celu symlinku.
Dlatego podpinamy **cały katalog**, nie sam plik `kitty.conf`:

```bash
rm -rf ~/.config/kitty        # tylko jeśli nie ma tam nic własnego
ln -s ~/.config/nvim/kitty ~/.config/kitty
```

Sprawdź, że motyw się wczytuje (powinno wypisać tło `Color(37, 38, 35)`, bez komunikatu
`Could not find included config file`):

```bash
kitty +runpy 'from kitty.config import load_config; import os
print(load_config(os.path.expanduser("~/.config/kitty/kitty.conf")).background)'
```

### 4a. Dolphin / menedżer plików: „Otwórz terminal tutaj” jako nowa karta (opcjonalnie)

`kitty.conf` ma `startup_session` (zapamiętane karty), który ignoruje folder przekazany przez
menedżer plików. `kitty/open-here.sh` to naprawia: jeśli kitty już działa, dodaje kartę w tym
folderze (przez gniazdo z `listen_on`); jeśli nie działa, startuje z zapamiętanymi kartami i
dokłada kartę w folderze. Aby KDE go używało, trzeba podmienić wpis `kitty.desktop`
(plik leży poza repozytorium):

```bash
sed "s#^Exec=kitty\$#Exec=$HOME/.config/kitty/open-here.sh#" /usr/share/applications/kitty.desktop \
    > ~/.local/share/applications/kitty.desktop
kbuildsycoca6          # odśwież cache KDE
```

W `~/.config/kdeglobals` powinno być `TerminalApplication=kitty` i `TerminalService=kitty.desktop`.
Po zmianie zrestartuj kitty (gniazdo powstaje przy starcie). KDE przekazuje folder tylko jako
katalog roboczy procesu, nie jako argument; skrypt obsługuje oba przypadki.

## 5. Font Monaspace Neon NF

`kitty.conf` ustawia `font_family Monaspace Neon NF`.

```bash
cd /tmp
curl -LO https://github.com/githubnext/monaspace/releases/download/v1.400/monaspace-nerdfonts-v1.400.zip
mkdir -p ~/.local/share/fonts/monaspace-neon-nf
unzip -j -o monaspace-nerdfonts-v1.400.zip "NerdFonts/Monaspace Neon/*.otf" -d ~/.local/share/fonts/monaspace-neon-nf
fc-cache -f ~/.local/share/fonts
fc-list : family | grep -i "monaspace neon nf"      # musi coś wypisać
```

## 6. Pierwsze uruchomienie Neovima

```bash
nvim
```

- `vim.pack` pobierze wtyczki (zatwierdź instalację, jeśli zapyta).
- Mason zainstaluje `roslyn`, `lua-language-server` i `stylua` (`ensure_installed` w `init.lua`).
  Jeśli Roslyn się nie zainstaluje: `:MasonInstall roslyn` (pakiet pochodzi z rejestru
  `Crashdummyy/mason-registry`, który jest już dodany w konfiguracji).
- Parsery treesitter mogą wymagać chwili na kompilację (`tree-sitter-cli` musi być w `$PATH`).
- Otwórz dowolny plik `.cs` w projekcie z `.sln`; Roslyn ładuje projekt kilkanaście sekund
  (postęp widać we fidget w rogu).

## 7. Weryfikacja

W Neovimie:

- `:checkhealth vim.lsp` — na pliku `.cs` w sekcji *Active Clients* ma być `roslyn`.
- `:colorscheme` — ma wypisać `bamboo`.
- `:checkhealth roslyn` — SDK >= 10 bez ostrzeżeń.

W terminalu: tło kitty to ciepły szary (`#252623`), a nie czarny. Jeśli jest czarne,
wróć do punktu 4.

## Czego repozytorium nie przenosi

- `kitty.desktop` w `~/.local/share/applications` (punkt 4a) i `~/.config/kdeglobals`.
- Sesje auto-session i historia undo (`~/.local/state/nvim`) są lokalne dla maszyny.
- Klucze SSH i ustawienia `~/.ssh`.
