
 Programme de création/modification d'un lanceur Linux

# Installation de DesktopCreator 

## Procédure automatique : 

[1] Téléchargez le fichier "Release_Github_Linux.tar.gz" dans les [Releases]

(https://github.com/myhumankit/DesktopCreator/releases/tag/V.1_2).

[2] Décompressez et lancez Script_install.sh (double-clic puis lancer)

                         ==================================

Compatibilité Linux de l'exécutable fourni (compilé sous Docker) :

Cet exécutable est fourni au format binaire autonome. Il a été compilé pour garantir une compatibilité maximale entre les différentes distributions.
 
    • Systèmes testés et supportés :
        ◦ Ubuntu : 20.04 LTS, 22.04 LTS, 24.04 LTS et versions ultérieures.

        ◦ Linux Mint : 20, 21, 22 et versions ultérieures.

        ◦ Debian : 11 (Bullseye), 12 (Bookworm) et versions ultérieures.

        ◦ Autres : Compatible avec la majorité des distributions utilisant GLIBC 2.31 ou supérieure.

    • Prérequis système : Aucune installation de Python n'est requise. Cependant, si l'interface ne s'affiche pas, assurez-vous que les bibliothèques graphiques de base sont présentes (généralement déjà installées sur les versions "Desktop") : libx11-6, libglib2.0-0.

                       =============================

    Pour en savoir plus sur le fonctionnement et l'usage de ce programme : 
                        cliquer sur :  menu/Aide/Guide.

                       =============================


Si vous devez compiler le programme, voici mes procédures de compilation :


## Compil avec PyInstaller :

cd ~/DOCUMENTS/Python/DesktopCreator
python3 -m venv venv
source venv/bin/activate


pip3 install pyinstaller
pip3 install FreeSimpleGui
pip3 install pillow


python -m PyInstaller DesktopCreator_1_2.py \
  --onefile \
  --noconsole \
  --add-data "lanceur.png:." \
  --hidden-import FreeSimpleGui \
  --hidden-import PIL._tkinter_finder



                       ------------------------------

## Compil sous Docker :

(pour être compatible avec anciennes versions Ubuntu, Mint, Debian)

cd ~/DOCUMENTS/Python/DesktopCreator/Compil_Docker

docker run --rm -v "$(pwd):/src" -w /src python:3.10-slim-bullseye /bin/bash -c "apt-get update && apt-get install -y binutils python3-tk && pip install --upgrade pip && pip install pyinstaller FreeSimpleGui Pillow && pyinstaller --onefile --windowed --icon=lanceur.png DesktopCreator_1_2.py"

sudo chown -R $USER:$USER dist build 

                       =============================



