#!/usr/bin/env bash
# Instala o ChromeOS-Fluent para o usuário atual (sem sudo).
set -euo pipefail
cd "$(dirname "$0")"
THEMES="$HOME/.themes"; BIN="$HOME/.local/bin"; UNIT="$HOME/.config/systemd/user"
mkdir -p "$THEMES" "$BIN" "$UNIT" "$HOME/.config/gtk-4.0" "$HOME/.local/share/fluent-theme-test"

echo "→ tema"; rm -rf "$THEMES/ChromeOS-Fluent"; cp -a theme/ChromeOS-Fluent "$THEMES/"
echo "→ scripts"; install -m755 bin/fluent-accent-sync bin/fluent-shot "$BIN/"; install -m644 tools/harness.py "$HOME/.local/share/fluent-theme-test/"
echo "→ libadwaita/GTK4 (links em ~/.config/gtk-4.0, com backup)"
for f in gtk.css gtk-dark.css; do
  t="$HOME/.config/gtk-4.0/$f"
  [ -e "$t" ] && [ ! -L "$t" ] && mv "$t" "$t.bak.$(date +%s)"
  ln -sfn "$THEMES/ChromeOS-Fluent/gtk-4.0/$f" "$t"
done
ln -sfn "$THEMES/ChromeOS-Fluent/gtk-assets" "$HOME/.config/gtk-4.0/assets"
echo "→ serviço que acompanha a cor de destaque"
install -m644 systemd/fluent-accent.service "$UNIT/"
systemctl --user daemon-reload; systemctl --user enable --now fluent-accent.service || true
"$BIN/fluent-accent-sync" --no-reload || true

echo "→ aplicando tema"
gsettings set org.gnome.desktop.interface gtk-theme 'ChromeOS-Fluent'
gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
gsettings set org.gnome.desktop.wm.preferences theme 'ChromeOS-Fluent'
gsettings set org.gnome.desktop.wm.preferences button-layout 'appmenu:minimize,maximize,close'
if gnome-extensions list | grep -q '^user-theme@'; then
  dconf write /org/gnome/shell/extensions/user-theme/name "'ChromeOS-Fluent'"
else echo "! Extensão User Themes ausente: o tema do Shell não será aplicado (veja o README)"; fi
if [ -d "$HOME/.local/share/icons/Tela-circle" ] || [ -d /usr/share/icons/Tela-circle ]; then
  gsettings set org.gnome.desktop.interface icon-theme 'Tela-circle-accent' || true
else echo "i Ícones Tela-circle não encontrados: opcional, veja o README"; fi
if [ "${1:-}" = "--extensions" ]; then dconf load /org/gnome/shell/extensions/ < config/extensions.dconf; fi
echo "Pronto. Reinicie os apps (nautilus -q) ou faça logout/login."
