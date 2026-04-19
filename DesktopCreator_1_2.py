import FreeSimpleGUI as sg
import os
from PIL import Image
import io
import sys
import subprocess
from pathlib import Path
import configparser
import webbrowser
import json
import locale

versionDC = "V_1.2 du 14 avril 2026"
OFFSET_THEME = 68           # hauteur en pixels de la barre de titre avec menu
chemin_lanceur = os.path.expanduser("~/.local/share/applications/")
chemin_systeme = os.path.abspath(os.path.expanduser("~/.local/share/applications"))
masque_erreur = False
fichier_exec = ""
nom_lanceur = ""
version_prog = ""
fichier_icone = ""
mode_terminal = False
ajout_menu = False
choix_cat = ""
action_fichier = ""
maj_lanceur = False
liste_categories = {}
titrelislang = ""
ListLang = []
LANGUES = {}
fichlang = ""
codlang = ""
langue = ""
liste_themes = sg.theme_list()
themes_sombres = [t for t in liste_themes if "Dark" in t or "Black" in t]
themes_clairs = [t for t in liste_themes if t not in themes_sombres]
themes_S = themes_sombres[::8]    # on en prend 1 sur 8
themes_C = themes_clairs[::8]     # on en prend 1 sur 8
DOSSIER_CONFIG = Path.home() / ".config" / "desktopcreator"
FICHIER_THEME = DOSSIER_CONFIG / "theme_pref.txt"    # fichier sauvegarde du thème choisi
FICHIER_MASQUE = DOSSIER_CONFIG / "masque_pref.txt"  # fich.sauvegarde masque affichage des erreurs des noms de desktops
FICHIER_LANGUE = DOSSIER_CONFIG / "langue_pref.txt"  # fich. sauvegarde langue choisie
TEXTES = {}

def safe_open_path(path):     # ouverture de dossier indépendant du compilateur
    # A utiliser si compilation avec Docker pour appel proces ou lien url
    # Lance une commande ou ouvre un chemin en nettoyant l'environnement.
    # 'commande' peut être un simple chemin (string) ou une liste [prog, arg]
    new_env = os.environ.copy()    # préparation d'un environnement propre
    if sys.platform.startswith('linux'):
        for var in ['LD_LIBRARY_PATH', 'PYTHONPATH', 'PYTHONHOME']:
            new_env.pop(var, None)
    try:
        if isinstance(path, str):   # C'est une chaîne de caractères (Dossier ou URL)
            if sys.platform == "win32":
                os.startfile(path)  # Sous Windows, on utilise 'os.startfile'
            else:
                subprocess.Popen(['xdg-open', path], env=new_env) # Sous Linux, on utilise 'xdg-open' avec l'environnement propre
        else:     # Sinon c'est une liste (p.ex. Lancement de l'IDE Arduino avec arguments)
            subprocess.Popen(path, env=new_env)  # Popen fonctionne sur Windows et Linux         
    except Exception as e:
        print(f"Erreur avec {path} : {e}")
        
def construire_menu(langue):
    return [
        [TEXTES.get("me_file", "File"), [
            TEXTES.get("me_close", "Close"),
            TEXTES.get("me_enable_case_errors", "Enable case-sensitivity errors")
        ]],
        
        [TEXTES.get("me_themes", "Themes"), [
            TEXTES.get("me_theme_dark", "Dark"), themes_S,
            TEXTES.get("me_theme_light", "Light"), themes_C
        ]],

        [TEXTES.get("me_help", "Help"), [
            TEXTES.get("me_about", "About"),
            TEXTES.get("me_guide", "Guide")
        ]],

        [f"🌐 {langue}", ['Lang.']],

        [' '*35, []],

        ['MHK', ["My Human Kit"]],
    ]

# Fonction de conversion de la catégorie affichée en catégorie système
def user_to_system_category(user_label):
    for key, value in TEXTES.items():
        if key.startswith("ca_") and value == user_label:
            return key[3:]   # enlève "ca_"
    return None

# Fonction de conversion de la catégorie système en catégorie affichée
def system_to_user(cat_systeme):
    return TEXTES.get("ca_" + cat_systeme, cat_systeme)

# Fonction de Gestion du thème d'affichage
def charger_theme():
    if FICHIER_THEME.exists():
        return FICHIER_THEME.read_text(encoding='utf-8').strip()
    return "DarkBlue"        # Thème par défaut si le fichier n'existe pas

def sauver_theme(nom_theme):
    try:
        DOSSIER_CONFIG.mkdir(parents=True, exist_ok=True)      # crée le dossier s'il n'existe pas
        FICHIER_THEME.write_text(nom_theme, encoding='utf-8')
    except Exception as e:
        mess_alerte(f"Échec de la sauvegarde du thème : {e}",False,False)

def theme_popup(theme):
    if "Dark" in theme or "Black" in theme:
        sg.theme('DarkAmber')     
    else:
        sg.theme('LightGrey1')

# Fonction de choix au cas où desktop existe déjà
def popup_choix_modif(contenu):
    theme_original = sg.theme()
    theme_popup(theme_original)
    layout_prev = [
        [sg.Text(TEXTES.get("ms_already_exists","Fichier {contenu} déjà présent").format(contenu=contenu),
                 font=("Helvetica", 12, "bold"))], 
        [sg.Text(TEXTES.get("ms_modify_launcher","Voulez-vous modifier ce lanceur ?"))],
        [sg.Button(TEXTES.get("bu_edit","Modifier"), button_color=('black', 'orange'), pad=((10, 0),(20, 10))),
             sg.Push(), sg.Button(TEXTES.get("bu_change_name","Changer le nom du nouveau lanceur"), button_color=('black', 'lightgreen'), pad=((10, 0),(20, 10)))],
    ]
    pop_win = sg.Window(TEXTES.get("di_confirmation","Confirmation"), layout_prev, modal=True)
    sg.theme(theme_original)
    event, _ = pop_win.read(close=True)   # _ pour dire qu'il n'y a pas de values à lire
    return event == TEXTES.get("bu_edit","Modifier")    # renvoit true (si cliqué sur Modifier) sinon False

# Fonction de lecture d'un desktop qui existe déjà
def lire_donnees_desktop(chemin_fichier):
    config = configparser.ConfigParser(interpolation=None)
    try:
        config.read(chemin_fichier, encoding='utf-8')
        if 'Desktop Entry' in config:
            section = config['Desktop Entry']
            return {
                "Terminal": section.get('Terminal', ''),  # chaîne vide par défaut si absent
                "Exec": section.get('Exec', ''),
                "Version": section.get('Version', ''),
                "Icon": section.get('Icon', ''),
                "Categories": section.get('Categories', ''),
                "Name": section.get('Name', '')
            }
    except Exception as e:
        print(f"Erreur lors de la lecture : {e}")
        return None

# Fonction d'affichage de l'à propos
def afficher_apropos(window_parent):
    global TEXTES    
    window_parent.refresh()
    x, y = window_parent.current_location()
    desc_apropos = TEXTES.get("about_text", """
           DesktopCreator 
        Programme développé
       sous Python3+FreeSimpleGUI
       et compilé avec Docker
       pour rétro-compatibilité.

       Auteur : Yves Le Chevalier
       Pour :  My Human Kit
       {version}""")
    desc_apropos = desc_apropos.format(version=versionDC)
    layout = [
        [sg.Frame('', [
            [sg.Multiline(desc_apropos, size=(33, 10), no_scrollbar=True)],
            [sg.Push(), sg.Button(TEXTES.get("bu_close", "Fermer"), key="-CLOSE_AP-"), sg.Push()],
            ], border_width=1)
        ]
    ]
    return sg.Window(TEXTES.get("about_win_title", "À propos"), layout, location=(x + 10, y - OFFSET_THEME + 10),
                     keep_on_top=True, finalize=True)

# Fonction d'affichage de l'aide
def afficher_aide(window_parent):
    global TEXTES
    window_parent.refresh()
    x, y = window_parent.current_location()
    w, h = window_parent.size
    desc_aide = TEXTES.get("help_text", """
                       Programme de création/modification d'un lanceur Linux.

  Le dossier standard de création d'un lanceur, lorsqu'on veut faire figurer le
  programme au menu Linux, est le dossier '~/.local/share/applications' proposé par
  défaut. Mais on peut choisir de créer le lanceur sur le bureau ou dans un autre
  dossier et il ne sera alors pas ajouté au menu Linux.
  Cliquer pour cela sur le bouton [Changer de dossier]
  
  S'il existe dans le dossier choisi des lanceurs dont le nom comporte des majuscules,
  un message d'information non bloquant sera affiché pour chacun d'eux.
  Il est possible de ne plus afficher ce message lorsque le cas se présentera en
  cliquant sur le bouton [Ne plus afficher].
  Pour rétablir l'affichage de ce type d'anomalie, il faut choisir dans le menu "Fichier"
  l'option "Activer les messages erreur de casse".

  Saisir ensuite le nom sous lequel apparaîtra le lanceur,
  (ne saisir que le nom, sans saisir le '.desktop'),  puis cliquer sur [OK].
  
  Si un lanceur existe déjà avec ce nom dans le dossier choisi, il vous est proposé
      soit : de changer de nom si c'est un nouveau programme
      soit : d'apporter des modifications au lanceur déjà existant sous ce nom.
      
  NB : quelle que soit la casse employée pour saisir le nom, celui-ci sera toujours
       converti automatiquement en minuscules. Si donc, vous avez déjà enregistré
       manuellement un lanceur avec un nom comportant des majuscules, il vous aura
       été signalé au moment du choix du dossier de stockage et il sera impossible
       de le modifier ici. Vous devrez donc le mettre en minuscules afin de respecter
       les conventions de nommage préconisées dans ce domaine.

  Il faut ensuite choisir l'exécutable (issu de la compilation du programme pour
  lequel vous voulez créer le lanceur) en cliquant sur le bouton [Exécutable ?].
  Si le programme choisi n'est pas un exécutable, un message d'erreur le signalera.

  La ligne suivante demande de saisir le numéro de version du programme. Il suffit
  généralement de reprendre celui-ci dans le nom de l'exécutable. Si on ne saisit
  pas de version celle-ci sera automatiquement attribuée avec la valeur 1_0.

  Il faut ensuite choisir l'icône du lanceur. Si le programme dispose d'une icône
  qui lui est propre, celle-ci devra avoir été copiée dans le dossier prévu à cet
  effet : /home/nom_utilisateur/.local/share/icons).
  Cette icône doit être une image PNG au format carré (souvent en 42x42 ou 64x64).
  Pour sélectionner l'une de ces icônes, cliquer sur le bouton [Icônes utilisateurs].
  Si on ne dispose pas d'une icône utilisateur pour ce programme, on clique alors
  sur le bouton [Autres icônes] pour afficher un choix d'icônes.
  Quel que soit le bouton cliqué, il est toujours possible d'accéder à d'autres icône
  à condition d'en connaître le dossier et le nom.
  L'image de l'icône choisie est ensuite affichée en regard de son chemin d'accès.

  Il faut ensuite indiquer si l'exécution doit être faite dans une fenêtre terminal
  en cliquant sur le bouton [NON] proposé par défaut. Il bascule alors à [OUI].

  L'étape suivante consiste à choisir la catégorie à laquelle le programme appartient
  en cliquant dans la liste déroulante qui s'affiche. Cette catégorie permet de
  classer les applications dans le menu Linux.

  A ce stade, il faut cliquer sur le bouton [Générer le lanceur].
  Ceci provoque l'affichage d'un aperçu du contenu du fichier desktop lanceur.
  On peut alors valider l'ensemble de la saisie en cliquant sur le bouton [Enregistrer].
  Si on constate, par contre, que l'on s'est trompé sur un élément, cliquer sur
  [Modifier] pour revenir à l'écran de saisie et faire les corrections voulues.

  A tout instant on peut s'interrompre en cliquant sur [Abandon] ou en fermant la
  fenêtre (X dans le coin supérieur droit).

  Le bouton MHK dans la barre de menu ouvre la page d'accueil du site My Human Kit.
""")
    layout = [
        [sg.Frame('', [
            [sg.Multiline(desc_aide, size=(70, 30), no_scrollbar=False,
                          border_width=4, disabled=True, font=("Arial", 12))],
            [sg.Push(), sg.Button(TEXTES.get("bu_close", "Fermer"), key="-CLOSE_HELP-"), sg.Push()],
            ], border_width=1)
        ]
    ]
    return sg.Window(TEXTES.get("help_win_title", "Aide"), layout, location=(x + w + 10, y - OFFSET_THEME), finalize=True)

# Fonction de prévisualisation du fichier desktop avant enregistrement
def popup_previsualisation(contenu):
    layout_prev = [
        [sg.Text(TEXTES.get("di_preview","Aperçu du fichier .desktop"), font=("Helvetica", 12, "bold"))],
        [sg.Multiline(contenu, size=(80, 10), font=("Courier", 12), disabled=True)],
        [sg.Text(TEXTES.get("ms_save_or_edit","Voulez-vous enregistrer ou modifier ce fichier ?"), font=("Helvetica", 12))],
        [sg.Button(TEXTES.get("bu_edit","Modifier"), button_color="red", pad=((10, 0),(20, 10))),
             sg.Push(),
             sg.Button(TEXTES.get("bu_save","Enregistrer"), key="-SAVEDESK-", button_color="green", pad=((10, 0),(20, 10)))],
    ]
    pop_win = sg.Window(TEXTES.get("di_confirmation","Confirmation"), layout_prev, modal=True)
    event, _ = pop_win.read(close=True)   # _ pour dire qu'il n'y a pas de values à lire
    return event == "-SAVEDESK-"         # renvoit true (si cliqué sur enregistrer) sinon False 

# Fonction de lecture et sauvegarde du masque d'affichage des erreurs de casse de desktops existants 
def sauver_masque(valeur_masque):
    try:
        DOSSIER_CONFIG.mkdir(parents=True, exist_ok=True)      # crée le dossier s'il n'existe pas
        # On transforme le booléen en texte "True" ou "False"
        FICHIER_MASQUE.write_text(str(valeur_masque), encoding='utf-8')
    except Exception as e:
        mess_alerte(f"Échec de la sauvegarde du masque : {e}",False,False)
        
def charger_masque():
    masque_erreur = False
    if FICHIER_MASQUE.exists():
        if FICHIER_MASQUE.read_text(encoding='utf-8').strip() == "True" :
            masque_erreur = True
    return masque_erreur

# fonction de sélection d'une icône avec previsualisation
def selecteur_icone(titre, message, mode_dossier, chemin_par_defaut):
    theme_original = sg.theme()
    sg.theme("DarkGrey14")
    icones_disponibles = []               # On liste les icônes PNG du dossier suggéré
    chemin_par_defaut = os.path.expanduser(chemin_par_defaut)
    if os.path.isdir(chemin_par_defaut):
        icones_disponibles = [f for f in os.listdir(chemin_par_defaut) if f.lower().endswith('.png')]
        icones_disponibles.sort()
    grille_layout = []     # Construction de la grille de miniatures 
    ligne = []
    for i, nom_icone in enumerate(icones_disponibles):
        chemin_complet = os.path.join(chemin_par_defaut, nom_icone)
        try:
            # On prépare la miniature pour la grille
            img = Image.open(chemin_complet)
            img.thumbnail((32, 32))
            bio = io.BytesIO()
            img.save(bio, format="PNG")
            
            # Chaque icône est un bouton d'image cliquable
            ligne.append(sg.Button("", image_data=bio.getvalue(), key=f"-ICONE_{nom_icone}-", 
                                   tooltip=nom_icone, button_color=(sg.theme_background_color(), sg.theme_background_color()), border_width=0))
        except:
            continue           
        if (i + 1) % 10 == 0:    # pour avoir plus ou moins d'icônes par ligne (10)
            grille_layout.append(ligne)
            ligne = []
    if ligne:
        grille_layout.append(ligne)
    layout_popup = [                          # Mise en page globale
        [sg.Text(titre, font=("Helvetica", 12, "bold"))],
        [sg.Text(message)],
        [sg.Text(TEXTES.get("la_folder", "Dossier {chemin}").format(chemin=chemin_par_defaut), font=("Helvetica", 8, "italic"))],
        # Zone défilante pour la galerie d'images
        [sg.Column(grille_layout, size=(450, 300), scrollable=True, vertical_scroll_only=True, background_color="#333333")],       
        [sg.Text(TEXTES.get("la_other_file","Ou choisir un autre fichier :"))],
        [sg.Input(key="-PATH-", size=(45, 1)), sg.FileBrowse(TEXTES.get("bu_browse", "Parcourir"), initial_folder=chemin_par_defaut)],        
        [sg.Button(TEXTES.get("bu_cancel", "Annuler"), button_color=('white','red')),
         sg.Push(),
         sg.Button(TEXTES.get("bu_ok","Valider"),key="-VALICO-", button_color=('black','LightGreen'))]
    ]
    pop_win = sg.Window(titre, layout_popup, modal=True, finalize=True)
    resultat = None
    while True:
        event, values = pop_win.read()        
        if event in (sg.WIN_CLOSED, TEXTES.get("bu_cancel", "Annuler")):
            break       
        if event.startswith("-ICONE_"):             # on clique sur une icône de la grille
            nom_fichier = event.replace("-ICONE_", "").rstrip("-")
            chemin_final = os.path.join(chemin_par_defaut, nom_fichier)
            pop_win["-PATH-"].update(chemin_final)
        if event == "-VALICO-":
            resultat = values["-PATH-"]
            if resultat:
                break
            else:
                sg.popup_error(TEXTES.get("ms_select_icon","Veuillez sélectionner une icône."))
    pop_win.close()
    sg.theme(theme_original)
    return resultat

# Fonction d'affichage d'un message d'erreur
def mess_alerte(message,masque,affichBout):
    if masque:
        return True
    theme_original = sg.theme()
    sg.theme('DarkRed')  
    layout_alerte = [
        [sg.Text("ATTENTION", font=("Helvetica", 14, "bold"))],
        [sg.Text(message, size=(60, None), auto_size_text=False)],
        [sg.Button(TEXTES.get("ms_dont_show_again","Ne plus afficher"), key="-MASQUER-", button_color=('white', 'grey'), visible=affichBout),
        sg.Push(), sg.Button(TEXTES.get("bu_ok","Compris"), key="-OK-", button_color=('white', 'green'))]
    ]
    win_err = sg.Window("", layout_alerte, modal=True, finalize=True, no_titlebar=False)

    while True :
        event, values = win_err.read()
        if event in (sg.WIN_CLOSED, "-OK-"):
            break
        if event == "-MASQUER-":
            masque = True
            break
    win_err.close()    
    sg.theme(theme_original)
    return masque           # renvoie la valeur de masque modifié ou non

# Fonction de contrôle de la casse des desktops déjà existants 
def controle_fichiers_desktop(repertoire):
    masque_erreur = charger_masque()
    sauv_masque = masque_erreur
    for fichier in os.listdir(repertoire):
        if fichier.endswith('.desktop'):
            nom_sans_extension = os.path.splitext(fichier)[0]
            if any(c.isupper() for c in nom_sans_extension) :
                message = (
                    TEXTES.get('ms_case_issue','Dossier comportant un fichier nommé avec des lettres majuscules :\n{fichier}').format(fichier=fichier)
                    + "\n" +
                    TEXTES.get("ms_not_blocking","Ceci n'est pas bloquant, mais vous ne pourrez pas le modifier")
                )
                masque_erreur = mess_alerte(message, masque_erreur, True)
                if masque_erreur != sauv_masque :
                    sauver_masque(masque_erreur)
             
# Fonction d'affichage popup de sélection
def selecteur(titre, message, mode_dossier=False):
    theme_original = sg.theme()
    theme_popup(theme_original)
    if mode_dossier :
        bouton_parcourir = sg.FolderBrowse(TEXTES.get("bu_browse", "Parcourir"))
    else :
        bouton_parcourir = sg.FileBrowse(TEXTES.get("bu_browse", "Parcourir"))
    layout_popup = [
        [sg.Text(titre, font=("Helvetica", 12, "bold"))],
        [sg.Text(message)],
        [sg.Input(key="-PATH-", size=(60, 1), expand_x=True), bouton_parcourir],
        [sg.Button(TEXTES.get("bu_cancel", "Annuler"), button_color=('black','red'), pad=((10, 0),(20, 10))),
             sg.Push(),sg.Button(TEXTES.get("bu_ok", "Valider"), button_color=('black','LightGreen'), pad=((10, 0),(20, 10)), bind_return_key=True),]
    ]
    pop_win = sg.Window(titre, layout_popup, modal=True)
    resultat = None
    while True:
        event, values = pop_win.read()
        if event in (sg.WIN_CLOSED, TEXTES.get("bu_cancel", "Annuler")):
            break
        if event == "-COPY-":
            sg.clipboard_set(values["-CHEMINDEFAUT-"])
        if event == TEXTES.get("bu_ok", "Valider"):
            resultat = values["-PATH-"]
            break       
    pop_win.close()
    sg.theme(theme_original)
    return resultat

# Fonction de test si un fichier est un exécutable
def est_executable(chemin):
    # Vérifie si le chemin existe ET si on a le droit d'exécution (X_OK)
    return os.path.isfile(chemin) and os.access(chemin, os.X_OK)

# Fonction d'affichage de l'icone choisie
def affich_icone(icone):
    try:
        img = Image.open(icone)
        img.thumbnail((48,48))  # On force la taille à 48x48 pixels    
        bio = io.BytesIO()      # On converti l'image en données lisibles par FreeSimpleGUI (en mémoire)
        img.save(bio, format="PNG")
        del img       # On libère la mémoire
        # On met à jour l'élément avec les DONNÉES (data) (et non pas le chemin (filename))
        window["-IMG_ICONE-"].update(data=bio.getvalue())
        window["la_icon"].update(TEXTES.get('la_icon',"Icône : {icone}").format(icone=icone))
        window["la_icon"].update(visible=True)
        window["-IMG_ICONE-"].update(visible=True)
        window["st_user_icons"].update(visible=False)
        window["st_other_icons"].update(visible=False)
        window["st_loading_slow"].update(visible=False)
        window["la_category"].update(visible=True)
        window["-CAT-"].update(visible=True)
        window["op_run_in_terminal"].update(visible=True)
        window["me_non"].update(visible=True)
        window["bu_create_launcher"].update(visible=True)
    except Exception as e:
        window["-IMG_ICONE-"].update(visible=False)
        window["la_icon"].update(TEXTES.get('ms_icon_not_found',"Icône non trouvée"))
        window["la_icon"].update(visible=True)

# Fonctions de Gestion de la langue
def charger_langue():
    if FICHIER_LANGUE.exists():
        return FICHIER_LANGUE.read_text(encoding='utf-8').strip()
    else :
        codretour = "EN"                # anglais par défaut
        codes_connus = [lang["code"] for lang in LANGUES]  # liste des codes langues connues
        loc = locale.getlocale()[0]   # récup de la localisation de l'ordi (ex: fr_FR)
        if loc:                       # fr_FR se compose de :  fr = langue, FR = pays      
            elements = loc.split('_') # transforme "fr_FR" en une liste ["fr", "FR"]
            langue_loc = elements[0].upper() # premier élément (langue) mis en majuscule
            if langue_loc in codes_connus:    
                codretour = langue_loc
            else: 
                if len(elements) > 1:              # vérifier qu'il y a un 2e élément (le pays)
                    pays_loc = elements[1].upper() # on le convertit en majuscule
                    if pays_loc in codes_connus:
                        codretour = pays_loc         # on prend le pays comme code langue
        return codretour

def sauver_langue(codlang):
    try:
        DOSSIER_CONFIG.mkdir(parents=True, exist_ok=True)      # crée le dossier s'il n'existe pas
        FICHIER_LANGUE.write_text(codlang, encoding='utf-8')
    except Exception as e:
        mess_alerte(f"Échec de la sauvegarde de la langue : {e}",False,False)

def code_from_name(name):
    for lang in LANGUES:
        if lang["name"] == name:
            return lang["code"]

def name_from_code(code):
    for lang in LANGUES:
        if lang["code"] == code:
            return lang["name"]
        
def file_from_name(name):
    for lang in LANGUES:
        if lang["name"] == name:
            return lang["file"]
        
def on_select_lang() :       # récup de la langues choisie
    global liste_categories
    global window_main
    langue = values["-LISLANG-"]
    window_main["-LISLANG-"].update(visible=False)
    codlang = code_from_name(langue)
    sauver_langue(codlang)
    fichlang = file_from_name(langue)
    x, y = window_main.current_location()
    nouvelle_pos = (x, y - OFFSET_THEME)        # remonter d'une ligne
    if window_main is not None:
        window_main.close()
        window_main = None
    window_main = creer_fenetre_principale(pos=nouvelle_pos)   # au même emplacement
    load_language(codlang)
    menu_def = construire_menu(langue)
    window_main["-MENU_BAR-"].update(menu_definition=menu_def)

def ChoixLangue():    # clic sur le bouton de changement de langue
    langue = name_from_code(codlang)
    window["-LISLANG-"].update(visible=True)
    window["-LISLANG-"].update(langue)
    
def load_language(codlang):
    global TEXTES
    global liste_categories
    langue = name_from_code(codlang)
    fichlang = file_from_name(langue)
    locparam=os.path.join(LocActu,"DeskTopCreatParam").replace("\\","/")
    filename=os.path.join(locparam,fichlang).replace("\\","/")
    try:
        with open(filename, "r", encoding="utf-8") as f:              
            TEXTES = json.load(f)
            liste_categories = [
                TEXTES["ca_Utility"],
                TEXTES["ca_Office"],
                TEXTES["ca_Education"],
                TEXTES["ca_Graphics"],
                TEXTES["ca_Network"],
                TEXTES["ca_Science"],
                TEXTES["ca_Game"],
                TEXTES["ca_AudioVideo"],
                TEXTES["ca_Development"],
                TEXTES["ca_Settings"],
                TEXTES["ca_System"]
            ]
            menu_def = construire_menu(langue) 
            window_main['-MENU_BAR-'].update(menu_definition=menu_def)
            window_main["-LADOSS-"].update(TEXTES.get("la_folder", "Dossier : {chemin}").format(chemin=chemin_lanceur)),
            # mise à jour de tous les champs avec une clé dans la langue choisie
            for cle, texte in TEXTES.items():
                if cle in window_main.AllKeysDict:
                    try:
                        window_main[cle].update(texte)    # On met à jour l'élément (Label, Bouton, Frame...)
                    except Exception as e:
                        print(f"Erreur de mise à jour pour {cle}: {e}")
    except IOError :
        TEXTES = {}
        mess_alerte(f"Attention : missing file: {fichlang}",False,False)

# fonction d'effacement ou d'affichage du cadre "la_save_location"
def efface_la_save_location() :
    window["bu_change_folder"].update(visible=False)
    window["-BTN_OK0-"].update(visible=False)
    window['-NOM-'].update(visible=True) 
    window['-BTN_OK-'].update(visible=True)
    window['la_launcher_name'].update(visible=True)

# fenêtre principale
def creer_fenetre_principale(pos=(None, None)):
    menu_def = construire_menu(langue)
    layout = [
        [sg.Menu(menu_def, key="-MENU_BAR-")],
        [sg.Combo(ListLang, key="-LISLANG-", font=("Helvetica", 10),pad=(170,0), size=(12,1),
                  visible=False, readonly=True, enable_events=True)],
        [sg.Frame("Où enregistrer le lanceur", [
            [sg.Text(TEXTES.get("la_folder", "Dossier : {chemin}").format(chemin=chemin_lanceur),
                     key="-LADOSS-", font=("Helvetica",12))],
            [sg.Button("Changer de dossier", key="bu_change_folder"),sg.Text(" "*60),
                     sg.Button("OK", key="-BTN_OK0-")],
        ], key="la_save_location")],
        [sg.pin(sg.Text("Nom du lanceur :", key="la_launcher_name",font=("Helvetica", 12), visible=False)),
            sg.pin(sg.Input(key='-NOM-', size=(20, None), font=("Helvetica", 12), visible=False, focus=True)),
            sg.pin(sg.Text("", key="-LANCEUR-", font=("Helvetica", 12), visible=False)),
            sg.pin(sg.Text(".desktop", key="-DESK-", font=("Helvetica", 12), visible=False)),
            sg.pin(sg.Button("OK", key="-BTN_OK-", visible=False)),
            sg.Push(),
            sg.pin(sg.Frame("",[
                [sg.Text("MODIFICATION", key="-MODIF-", font=("Helvetica", 12, "bold"), 
                     text_color='white', background_color='red')],
                ], key="-CADRE_MODIF-", relief=sg.RELIEF_SUNKEN, border_width=3, visible=False)),
            sg.Text("", size=(1, 1)),    #  Texte fictif pour que le sg.Push fonctionne pour -MODIF-
        ],      
        [sg.Button("Executable ?", key="op_executable", visible=False)],
        [sg.Text(f"Executable : {fichier_exec}", key="la_executable", font=("Helvetica", 12), visible=False)],
        [sg.Text("Version :", key="la_version",font=("Helvetica", 12), visible=False),             
             sg.Input(key='-VERS-', size=(8, None), font=("Helvetica", 12), visible=False),
             sg.Text("", key="-VERSION-", font=("Helvetica", 12), visible=False),
             sg.Button("OK", key="-BTN_OK1-", visible=False)],
        [sg.Button("Icônes utilisateur", key="st_user_icons", visible=False),
             sg.Button("Autres icônes", key="st_other_icons", visible=False),
             sg.Text("(un peu plus long à afficher)", key="st_loading_slow", font=("Helvetica", 10), visible=False),
             ],
        [sg.Text(f"Icône : {fichier_icone}", key="la_icon", font=("Helvetica", 12), visible=False),
            sg.Image(key="-IMG_ICONE-", size=(48, 48), visible=False, background_color='white')],
        [sg.Text("Ouvrir dans un terminal ?", key="op_run_in_terminal", font=("Helvetica", 12), visible=False),
            sg.Button("NON", key="me_non", size=(5, 1), visible=False)],
        [sg.Text("Catégorie :", key="la_category", font=("Helvetica", 12), visible=False),
            sg.Combo(liste_categories, key="-CAT-", font=("Helvetica", 12), readonly=True, visible=False)],
        [sg.Button("Abandon", key="me_abort", button_color='red', pad=((10, 0),(20, 10))),
            sg.Push(),
            sg.Button("Générer le lanceur", key="bu_create_launcher", button_color=('white', 'green'), pad=((0, 10), (20, 10)), visible=False)]
    ]
    return sg.Window("DesktopCreator", layout, location=pos, finalize=True)

theme_actuel = charger_theme()          
sg.theme(theme_actuel)

screen_w, screen_h = sg.Window.get_screen_size()   # taille de l'écran
pos = (                         # position de la fenêtre principale
    screen_w // 3 - 300,  # décalage gauche
    screen_h // 3 - 50    # décalage haut
)               
window_main = creer_fenetre_principale(pos)
window_main.refresh()
x, y = window_main.current_location()
w, h = window_main.size
window_aide = None
window_apropos = None

LocActu=os.path.abspath(os.getcwd())           # recup du repertoire courant
locparam=os.path.join(LocActu,"DeskTopCreatParam").replace("\\","/")
filename=os.path.join(locparam,"langues.json")
try:
    with open(filename, "r", encoding="utf-8") as f:
        datlang = json.load(f)
except IOError:
    mess_alerte((f"ERROR : missing file langues.json\n{filename}"),False,False)
else :    
    LANGUES = datlang["langages"]    
    ListLang = [lang["name"] for lang in LANGUES]
    window_main['-LISLANG-'].update(values=ListLang)
    codlang = charger_langue()
    langue = name_from_code(codlang)
    fichlang = f"lang_{codlang}.json"
    load_language(codlang)

while True:  
    window, event, values = sg.read_all_windows(timeout=100)
    if event not in (None, sg.TIMEOUT_KEY):
        print(f"L'événement reçu est : '{event}'")      # Pour voir quel évènement a été reçu
    if window == window_apropos :          # traitement des évènements de la fenêtre a propos
        if event in (sg.WIN_CLOSED, "-CLOSE_AP-"):
            window_apropos.close()
            window_apropos = None

    if window == window_aide :          # traitement des évènements de la fenêtre aide
        if event in (sg.WIN_CLOSED, "-CLOSE_HELP-"):
            window_aide.close()
            window_aide = None
            
    if window == window_main :          # traitement des évènements de la fenêtre principale           
        if event in (sg.WIN_CLOSED,'me_abort','me_close',"Close"):
            window_main.close()
            if window_aide:
                window_aide.close()
                window_aide = None
            if window_apropos :
                window_apropos.close()
                window_apropos = None
            break

        # Gestion des Thèmes
        if event in sg.theme_list():
            x, y = window.current_location()  # mémorise la position de la fenêtre 
            nouvelle_pos = (x, y - OFFSET_THEME)        # remonter d'une ligne
            sauver_theme(event)
            sg.theme(event)                          # applique le thème
            window_main.close()
            window_main = creer_fenetre_principale(pos=nouvelle_pos) # réouvre la fenêtre à la même position
            load_language(codlang)

        # Gestion de l'Aide
        if event == TEXTES.get("me_about", "A propos"):
            if window_apropos is None :
                window_apropos = afficher_apropos(window_main)
            else:
                window_apropos.bring_to_front()

        if event == TEXTES.get("me_guide","Guide") :
            if window_aide is None :
                window_aide = afficher_aide(window_main)
            else:
                window_aide.bring_to_front()     # remonte au devant la fenêtre déjà ouverte

        if event == "My Human Kit" :
            safe_open_path("https://myhumankit.org/")

        if event == TEXTES.get("me_enable_case_errors","Activer les messages erreur de casse") :
            sauver_masque(False)

        if event == "Lang." :
            ChoixLangue()

        if event == "-LISLANG-" :
            on_select_lang()
            
        if event == "bu_change_folder" :
            nouveau = selecteur(TEXTES.get("ms_tit_sel","Dossier de stockage"),
                                TEXTES.get("ms_select_save_location","Où voulez-vous enregistrer le lanceur ?"), True)
            if nouveau:
                chemin_lanceur = nouveau
                window["-LADOSS-"].update(TEXTES.get("la_folder","Dossier : {chemin}").format(chemin=chemin_lanceur))
                controle_fichiers_desktop(chemin_lanceur)
            efface_la_save_location()

        if event == "-BTN_OK0-":
            efface_la_save_location()
             
        if event == "-BTN_OK-":
            if values['-NOM-']:
                nom_lanceur = values['-NOM-'].strip().lower()
                window['-NOM-'].update(nom_lanceur)     # réaffichage du nom en minuscules
                window["-NOM-"].update(visible=False)
                window["-BTN_OK0-"].update(visible=False)
                window['-LANCEUR-'].update(nom_lanceur+".desktop")
                window['-LANCEUR-'].update(visible=True)
                window['-DESK-'].update(visible=False)
                nom1 = nom_lanceur.strip()+".desktop"
                chemin1 = Path(chemin_lanceur)/nom1
                if chemin1.exists():
                    if popup_choix_modif(nom1):          #  l'utilisateur veut modifier le lanceur existant
                        maj_lanceur = True
                        donnees = lire_donnees_desktop(chemin1)
                        if donnees:
                            fichier_exec = donnees['Exec']
                            window['la_executable'].update(fichier_exec)
                            window['la_icon'].update(donnees['Icon'])
                            window['-VERS-'].update(donnees['Version'])
                            nom_lanceur = donnees['Name']
                            version_prog = donnees['Version']
                            fichier_icone = donnees['Icon']
                            affich_icone(fichier_icone)
                            if donnees['Terminal'] == True :
                                window["me_non"].update(TEXTES.get("me_oui","OUI"))
                                mode_terminal = "True"
                            else :
                                window["me_non"].update(TEXTES.get("me_non","NON"))
                                mode_terminal = "False"
                            categ_lue = donnees['Categories'].rstrip(';')    # on supprime le ; final
                            if categ_lue == "System;Settings":
                                categ_lue = "System"
                            categorie_affichee = system_to_user(categ_lue)
                            window["-CAT-"].update(values=liste_categories)   # liste complète
                            window["-CAT-"].update(value=categorie_affichee)  # valeur lue dans le fichier
                            window["-BTN_OK-"].update(visible=False)
                            window["-CADRE_MODIF-"].update(visible=True)
                            window["-MODIF-"].update(visible=True)
                            window["op_executable"].update(visible=True)
                            window["la_executable"].update(visible=True)
                            window["st_user_icons"].update(visible=True)
                            window["st_other_icons"].update(visible=True)
                            window["st_loading_slow"].update(visible=True)
                            window["la_executable"].update(visible=True)
                            window["la_version"].update(visible=True)
                            window["-VERS-"].update(visible=True)
                            window["-BTN_OK1-"].update(visible=True)
                        else:
                            sg.popup_error(TEXTES.get("ms_read_error","Impossible de lire le contenu du fichier."))
                    else:                           # l'utilisateur veut changer le nom du lanceur
                        window['-NOM-'].update("")  # on vide juste le champ nom pour le re-saisir
                        window["-NOM-"].update(visible=True)
                        window['-DESK-'].update(visible=True)
                        window["-LANCEUR-"].update(visible=False)
                        window["-BTN_OK-"].update(visible=True)
                        window["-MODIF-"].update(visible=False)
                else:                               # c'est un nouveau nom de lanceur 
                    window["-BTN_OK-"].update(visible=False)
                    window["op_executable"].update(visible=True)
                    window["-NOM-"].update(disabled=True)
            else:
                mess_alerte(TEXTES.get("ms_enter_name", "Veuillez saisir un nom pour le lanceur."),False,False)
                
        if event == "op_executable":
            choix = selecteur(TEXTES.get("di_file_selection","Sélection de fichier"),
                              TEXTES.get("bu_select_executable","Sélectionner le fichier exécutable :"),False)
            if choix:
                if est_executable(choix) :
                    fichier_exec = choix
                    window["la_executable"].update(TEXTES.get('la_executable','Executable : {fichier_exec}').format(fichier_exec=fichier_exec))
                    window["op_executable"].update(visible=False)
                    window["la_executable"].update(visible=True)
                    window["la_version"].update(visible=True)
                    window["-VERSION-"].update(visible=False)
                    window["-VERS-"].update(visible=True)
                    window["-BTN_OK1-"].update(visible=True)
                else:
                    mess_alerte(TEXTES.get("ms_invalid_executable","Le fichier choisi n'est pas un fichier exécutable\n\
Avez vous autorisé l'exécution du fichier ? (Propriétés/Droits/Exécution)"),False,False)

        if event == "-BTN_OK1-":
            if values['-VERS-']:
                version_prog = values['-VERS-'].strip()
            else:
                version_prog = "1_0"
                window["-VERS-"].update(version_prog)
                mess_alerte(TEXTES.get("ms_default_version","Par défaut le n° de version sera {version}").format(version=version_prog)
                            ,False,False)
            window["-VERSION-"].update(version_prog)
            window["-VERSION-"].update(visible=True)
            window["-VERS-"].update(visible=False)
            window["-BTN_OK1-"].update(visible=False)
            window["st_user_icons"].update(visible=True)
            window["st_other_icons"].update(visible=True)
            window["st_loading_slow"].update(visible=True)
            window["-CAT-"].update(values=liste_categories)

        if event == "st_user_icons":
            choix = selecteur_icone(TEXTES.get("di_icon_selection","Sélection de l'icône"),
                                    TEXTES.get("ms_select_png", "Choisissez une image (.png) :"), False, "~/.local/share/icons")
            if choix:
                if choix.lower().endswith('.png'):
                    fichier_icone = choix
                    affich_icone(fichier_icone)   
                else:
                    mess_alerte(TEXTES.get("ms_invalid_png", "Veuillez sélectionner un fichier au format .png"),False,False)

        if event == "st_other_icons":
            choix = selecteur_icone(TEXTES.get("di_icon_selection","Sélection de l'icône"),
                                    TEXTES.get("ms_select_png","Choisissez une image (.png) :"), False, "/usr/share/icons/Mint-Y/apps/48")
            if choix:
                if choix.lower().endswith('.png'):
                    fichier_icone = choix
                    affich_icone(fichier_icone)   
                else:
                    mess_alerte(TEXTES.get("ms_invalid_png","Veuillez sélectionner un fichier au format .png"),False,False) 
            
        if event == "me_non":
            mode_terminal = not mode_terminal    # inversion 
            if mode_terminal:
                window["me_non"].update(TEXTES.get("me_oui","OUI"))
            else:
                window["me_non"].update(TEXTES.get("me_non","NON"))
                
        if event == "bu_create_launcher":
            if (os.path.abspath(chemin_lanceur) == chemin_systeme) :
                ajout_menu = True
            else :
                ajout_menu = False
            choix_cat = values["-CAT-"]
            cat_systeme =  user_to_system_category(choix_cat)   # on supprime les 3 premiers caracters (ca_)
            if cat_systeme == "System":
                cat_systeme = "System;Settings"
            if not choix_cat or choix_cat == "":
                mess_alerte(TEXTES.get("ms_missing_category","Erreur : Vous devez choisir une catégorie pour le lanceur !"),False,False)
                continue
            else:
                contenu_desktop = f"""[Desktop Entry]
Version={version_prog}
Type=Application
Name={nom_lanceur}
Exec={fichier_exec}
Icon={fichier_icone}
Terminal={str(mode_terminal).lower()}
Categories={cat_systeme};
"""
                confirmation = popup_previsualisation(contenu_desktop)   #renvoie true ou false)
                if confirmation:
                    nom_fichier = nom_lanceur.replace(" ", "_").lower() + ".desktop"
                    chemin_final = os.path.join(chemin_lanceur, nom_fichier)
                    try:
                        with open(chemin_final, "w", encoding='utf-8') as f:  
                            f.write(contenu_desktop) 
                        os.chmod(chemin_final, 0o755)   # 0o755 donne droits d'execution pour Gnome ou KDE
                        if maj_lanceur : 
                            action_fichier = TEXTES.get("ms_updated","mis à jour")
                        else : 
                            action_fichier = TEXTES.get("ms_created","créé")
                        if ajout_menu :
                            new_env = os.environ.copy()    # nettoyage environnement pour compil avec Docker
                            for var in ['LD_LIBRARY_PATH', 'PYTHONPATH', 'PYTHONHOME']:
                                new_env.pop(var, None)  # supprime ces variables (que PyInstaller a pu modifier) si elles existent
                            try:
                                subprocess.run(["update-desktop-database", chemin_systeme], check=True, env=new_env)   # maj du menu linux
                                action_menu = TEXTES.get("ms_added_to_menu","et le programme a été ajouté au menu Linux.")
                            except Exception as e:
                                mess_alerte(TEXTES.get("ms_menu_update_failed", "Note : Échec de la mise à jour du menu (non critique) :").format(error=e),False,False)
                                action_menu = TEXTES.get("ms_not_added_to_menu","mais le programme n'a pas pu être ajouté au menu Linux.")
                        else:
                            action_menu = TEXTES.get("ms_saved_without_menu","sans qu'il soit ajouté au menu Linux.")
                            mess_alerte(TEXTES.get("ms_launcher_done", "Le lanceur '{nom_fichier}' a bien été {action_fichier} \ndans le dossier {chemin_lanceur}\n{action_menu}").format(
                                    nom_fichier=nom_fichier,action_fichier=action_fichier,
                                    chemin_lanceur=chemin_lanceur,action_menu=action_menu),
                                    False,False)
                    except Exception as e:
                        print("DEBUG exception:", repr(e))
                        mess_alerte(TEXTES.get("ms_write_error", "Erreur d'écriture :\n{error}").format(error=e),False,False)
                    break
                else:                         # l'utilisateur veut modifier la saisie
                    if maj_lanceur :
                        window["-BTN_OK-"].update(visible=False)
                        window["-NOM-"].update(visible=False)
                        window['-DESK-'].update(visible=False)
                        window["-LANCEUR-"].update(visible=True) 
                    else :
                        window["-BTN_OK-"].update(visible=True)
                        window["-NOM-"].update(visible=True)
                        window["-NOM-"].update(disabled=False)
                        window['-DESK-'].update(visible=True)
                        window["-LANCEUR-"].update(visible=False)   
                    window["bu_change_folder"].update(visible=True)                  
                    window["op_executable"].update(visible=True)
                    window["la_executable"].update(visible=True)
                    window["la_version"].update(visible=True)
                    window["-VERSION-"].update(visible=False)
                    window["-VERS-"].update(visible=True)
                    window["-BTN_OK1-"].update(visible=True)
                    window["st_user_icons"].update(visible=True)
                    window["st_other_icons"].update(visible=True)
                    window["st_loading_slow"].update(visible=True)
                    
    elif window == window_aide :     # traitement des évènements de la fenêtre aide
        if event in (sg.WIN_CLOSED, "Fermer"):
            window_aide.close()
            window_aide = None
            
    elif window == window_apropos :     # traitement des évènements de la fenêtre à propos
        if event in (sg.WIN_CLOSED, "Fermer"):
            window_apropos.close()
            window_apropos = None

            
window_main.close()
