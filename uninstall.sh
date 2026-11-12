#!/usr/bin/env bash
# Remove o ChromeOS-Fluent e volta ao Adwaita.
set -u
systemctl --user disable --now fluent-accent.service 2>/dev/null
rm -f ~/.config/systemd/user/fluent-accent.service ~/.local/bin/fluent-accent-sync ~/.local/bin/fluent-shot
rm -rf ~/.themes/ChromeOS-Fluent ~/.local/share/fluent-theme-test ~/.local/share/icons/Tela-circle-accent
for f in gtk.css gtk-dark.css assets; do [ -L ~/.config/gtk-4.0/$f ] && rm -f ~/.config/gtk-4.0/$f; done
gsettings reset org.gnome.desktop.interface gtk-theme
gsettings reset org.gnome.desktop.interface icon-theme
gsettings reset org.gnome.desktop.wm.preferences theme
dconf reset /org/gnome/shell/extensions/user-theme/name
echo "Removido. Faça logout/login."
