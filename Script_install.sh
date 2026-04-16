#!/bin/bash

# --- Gestion du terminal ---
if [[ ! -t 1 ]]; then
  for term in x-terminal-emulator gnome-terminal konsole xterm; do
    if command -v "$term" >/dev/null 2>&1; then
      exec "$term" -e "$0"
      exit
    fi
  done
fi

# --- On se place là où est le script ---
# C'est la clé : maintenant "." désigne le dossier d'installation, peu importe où il est.
cd "$(dirname "$0")"

# --- Chemins SOURCES (Relatifs au script) ---
# On assume que ces fichiers sont dans le même dossier que ce script .sh
FICHEXE="./DesktopCreator_1_2" 
PARAM="./DeskTopCreatParam"
ICONE="./lanceur.png"

# --- Chemins DESTINATIONS (Toujours absolus car dans le système) ---
DESTEXE="$HOME/Applications"
DESTPARAM="$HOME/"
DESTICONE="$HOME/.local/share/icons"
DESTLANCEUR="$HOME/.local/share/applications"

# === Couleurs ===
GREEN="\e[32m"
YELLOW="\e[33m"
NC="\e[0m"

echo -e "${YELLOW}==============================================${NC}"
echo -e "${YELLOW}   Installation de DesktopCreator v1.2${NC}"
echo -e "${YELLOW}==============================================${NC}"

# === Création des dossiers de destination ===
mkdir -p "$DESTEXE"
mkdir -p "$DESTICONE"
mkdir -p "$DESTLANCEUR"

# === Copie des fichiers ===
# On vérifie si les sources existent avant de copier pour éviter les messages d'erreur moches
if [ -f "$FICHEXE" ]; then
    cp -f "$FICHEXE" "$DESTEXE/"
    # On rend l'exécutable... exécutable !
    chmod +x "$DESTEXE/$(basename "$FICHEXE")"
    echo -e "Exécutable : ${GREEN}Installé${NC}"
else
    echo -e "Exécutable : ${RED}Source introuvable !${NC}"
fi

[ -d "$PARAM" ] && cp -r "$PARAM" "$DESTPARAM" && echo -e "Paramètres : ${GREEN}Installés${NC}"
[ -f "$ICONE" ] && cp -f "$ICONE" "$DESTICONE/" && echo -e "Icône : ${GREEN}Installée${NC}"

## === Création du lanceur ===
cat <<EOF > "$DESTLANCEUR/desktopcreator.desktop"
[Desktop Entry]
Type=Application
Name=DesktopCreator
Comment=Lanceur créé par l'installateur
Exec=$HOME/Applications/DesktopCreator_1_2
Icon=$HOME/.local/share/icons/lanceur.png
Terminal=false
Categories=Utility;Development;
EOF

# === Finalisation des droits et rafraîchissement ===
# 1. On rend l'exécutable bien... exécutable
chmod +x "$DESTEXE/DesktopCreator_1_2"
# 2. On donne les droits au lanceur .desktop
chmod +x "$DESTLANCEUR/desktopcreator.desktop"
# 3. On force le système à voir la nouvelle application immédiatement
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESTLANCEUR" >/dev/null 2>&1
fi

echo -e "\n${GREEN}  Installation terminée ${NC}"
echo ""
read -p "Appuyez sur Entrée pour quitter..."


