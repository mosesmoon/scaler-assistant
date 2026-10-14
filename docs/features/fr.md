# Assistant HelixSR — Guide des fonctionnalités

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · **Français** · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

L'**Assistant HelixSR** est un outil de bureau Linux qui installe, change de méthode, met à jour et retire **[HelixSR](https://github.com/lonewolf0622/HelixSR)** dans vos jeux Steam en un clic, et indique pendant que vous jouez si HelixSR fonctionne réellement.

HelixSR exécute le réseau de mise à l'échelle DLSS Model E de NVIDIA sur les GPU AMD (RDNA 1 et plus récents) sous forme de shaders de calcul Direct3D 12 ordinaires, via Proton.

## À qui s'adresse-t-il ?

HelixSR n'a ni options de lancement ni fichier de réglages central. Il place des DLL dans le dossier de chaque jeu, selon l'une de trois méthodes par jeu. À la main, il faut :

1. Trouver quelles mises à l'échelle chaque jeu embarque (FSR 3.1, DLSS, XeSS, FSR 2) et où se trouve son `.exe` principal.
2. Choisir la bonne méthode, renommer les fichiers du jeu pour les garder en sécurité et copier les fichiers de HelixSR aux bons endroits.
3. Pour la méthode OptiScaler, inscrire les bons chemins dans `OptiScaler.ini`.
4. Tout refaire à chaque mise à jour de HelixSR, et encore quand une mise à jour du jeu écrase HelixSR.
5. Ouvrir `helixsr.log` pour savoir si HelixSR tourne vraiment.

L'Assistant HelixSR fait tout cela depuis une seule fenêtre. L'installation de HelixSR interroge jeu par jeu dans un terminal ; l'Assistant HelixSR les affiche dans une liste cliquable.

## Avant de commencer

> ⚠ **L'Assistant HelixSR n'inclut pas HelixSR et ne le télécharge jamais pour vous.** Il copie seulement des fichiers depuis le dossier HelixSR que vous avez préparé vous-même.

1. **Téléchargez HelixSR** (1.8.0 ou plus récent) depuis ses [versions GitHub](https://github.com/lonewolf0622/HelixSR/releases) et extrayez-le dans un dossier que vous conservez, par exemple votre dossier personnel.
2. **Lancez une fois `./helixsr-setup.sh` dans ce dossier.** Il demande l'autorisation de télécharger la DLL DLSS de NVIDIA et construit à partir d'elle le réseau de HelixSR (environ une minute). Quand il commence à poser des questions sur les jeux, vous pouvez répondre `n` ou fermer la fenêtre : l'Assistant HelixSR s'occupe des jeux. Si le dossier est trouvé mais pas encore préparé, l'Assistant propose un bouton « Lancer l'installation dans un terminal ».
3. **Un GPU AMD RDNA 1 ou plus récent** (Radeon RX 5000 et plus récentes, Steam Deck, APU Ryzen à graphismes RDNA). La prise en charge de Radeon Vega est expérimentale dans HelixSR 1.9.0.
4. **Des jeux Direct3D 12 lancés via Proton** qui embarquent FSR 3.1, DLSS, XeSS ou FSR 2.

Au premier démarrage, l'Assistant HelixSR cherche un dossier HelixSR préparé dans vos dossiers personnel, Téléchargements, Bureau et Games. Vous pouvez toujours en choisir un autre avec « Choisir le dossier de HelixSR… » ou en cliquant sur l'indicateur HelixSR en haut.

## Les trois méthodes pour intégrer HelixSR à un jeu

Ce sont les trois méthodes de HelixSR lui-même (les lettres sont les réponses utilisées par son installation). L'Assistant HelixSR ne propose que celles qui fonctionnent pour chaque jeu, la méthode par défaut en premier.

| Méthode | Le jeu doit avoir | Ce qui change dans le dossier du jeu | À choisir dans le jeu |
|---|---|---|---|
| **Méthode FSR** (f, par défaut pour les jeux FSR 3.1) | FSR 3.1 | Le `amd_fidelityfx_upscaler_dx12.dll` (ou `amd_fidelityfx_dx12.dll`) du jeu est remplacé par HelixSR ; le fichier du jeu est conservé sous `*.original.dll` | **AMD FSR** |
| **Méthode OptiScaler** (o) | DLSS, XeSS ou FSR 2 | OptiScaler (la version officielle de votre dossier HelixSR) à côté du `.exe` du jeu, son moteur FSR 3.1 pointant vers un dossier `HelixSR` voisin ; tout ce qu'il remplace va dans `HelixSR/backup` | **DLSS** (FSR ou XeSS fonctionnent aussi) |
| **Méthode DLSS** (d, expérimentale) | DLSS | Le chargeur DLSS de HelixSR en `dxgi.dll` et HelixSR en `nvngx.dll` à côté du `.exe` du jeu | **DLSS** |

## Fonctionnalités

### 1. Analyse de vos jeux Steam et de leurs mises à l'échelle

- Au premier démarrage, toutes les bibliothèques Steam sont analysées (y compris sur d'autres disques). Après avoir installé des jeux, cliquez sur « ⟳ Réanalyser les jeux Steam ».
- Le dossier de chaque jeu est fouillé à la recherche de DLL FSR 3.1, DLSS, XeSS et FSR 2, et le dossier de son `.exe` principal est trouvé grâce aux informations de lancement de Steam (lanceurs et `*-Shipping.exe` d'Unreal gérés).
- Les jeux avec **anti-triche** (Easy Anti-Cheat, BattlEye) sont signalés.
- Les noms de jeux suivent la langue de l'interface (noms localisés de Steam) et sont triés selon cette langue. Les jeux pouvant utiliser HelixSR passent en premier ; le filtre « Jeux pouvant utiliser HelixSR » est actif par défaut.

### 2. Installation en un clic

- « Installer HelixSR » installe avec la méthode par défaut ; la flèche à côté propose les autres. Chaque méthode indique ce qu'il faut choisir dans le jeu.
- Avant toute modification, l'outil vérifie que le dossier HelixSR est préparé (réseau construit) et que le jeu n'est pas lancé.
- La méthode DLSS explique d'abord ses risques et demande confirmation. Les jeux avec anti-triche demandent aussi confirmation.
- Ensuite, le journal indique précisément quels fichiers ont été remplacés, où les fichiers du jeu sont conservés et quoi choisir dans le jeu.

### 3. Changer de méthode, mettre à jour et réparer

- **Changer** : « Plus » → « Passer à la … » retire d'abord la méthode actuelle (en remettant tout en place) puis installe la nouvelle. Vos réglages de HelixSR suivent le jeu.
- **Mettre à jour** : quand votre dossier HelixSR contient une version plus récente que celle d'un jeu (nouvelle version de HelixSR ou réseau reconstruit), le jeu affiche « ↑ HelixSR … disponible » et un bouton « ↑ Mettre à jour » ; « ↑ Tout mettre à jour » traite tous les jeux d'un coup.
- **Réparer** : une mise à jour du jeu ou « Vérifier l'intégrité des fichiers du jeu » dans Steam peut remettre les fichiers du jeu par-dessus HelixSR. Le jeu explique alors ce qui s'est passé et affiche un bouton « Réparer », qui remet HelixSR en place et conserve les nouveaux fichiers du jeu comme sauvegarde.
- Quand un dossier HelixSR plus récent et préparé apparaît dans vos Téléchargements (ou un autre emplacement habituel), l'outil propose une fois de l'utiliser.

### 4. Retirer

- « Retirer » enlève HelixSR et remet chaque fichier qu'il a remplacé ou déplacé exactement comme avant.
- Les réglages de HelixSR du jeu (`helixsr.ini`) sont conservés, sauf si vous cochez « Retirer aussi les réglages de HelixSR de ce jeu ».
- Les fichiers que vous avez placés vous-même dans le dossier `my-fsr` du jeu ne sont jamais supprimés.

### 5. Réglages de HelixSR sans modifier de fichier

« ⚙ Réglages » modifie le `helixsr.ini` du jeu au moyen d'un formulaire. Seuls les réglages documentés dans le README de HelixSR sont proposés :

| Groupe | Réglage | Valeurs |
|---|---|---|
| Netteté | Filtre de netteté | Par défaut, Désactivé, NVIDIA, RCAS |
| | Intensité | 0.00 – 1.00 |
| | Suivre le curseur de netteté du jeu | Par défaut, Oui, Non |
| Mise à l'échelle (HelixSR 1.9.0+) | Réseau int8 | Par défaut (auto), Auto, Activé, Désactivé |
| | Dernière passe en Ultra Performance | Par défaut (Lanczos), Lanczos, EASU (FSR 1) |
| Compatibilité | Taille des vagues | Par défaut, 64, 32 |

« Par défaut » omet la ligne : HelixSR utilise alors sa propre valeur. Les commentaires et toutes les autres lignes du fichier restent tels quels. Le fichier est écrit à côté de la DLL de HelixSR selon la méthode du jeu (dossier `HelixSR` du jeu, à côté de la DLL FSR du jeu ou à côté du `.exe`).

### 6. État de HelixSR en direct (ce qui tourne vraiment)

Les jeux Steam en cours sont vérifiés toutes les 3 secondes :

- Proton charge les DLL Windows depuis leurs fichiers ; l'outil voit donc dans `/proc/<pid>/maps` si le jeu a **vraiment chargé HelixSR** (ainsi qu'OptiScaler ou le chargeur DLSS).
- HelixSR n'est chargé que lorsque le jeu utilise la mise à l'échelle. « HelixSR pas encore chargé » vous dit donc quoi choisir dans les réglages graphiques du jeu.
- Le `helixsr.log` de la session en cours est lu : la taille des vagues des noyaux du réseau et les éventuelles lignes d'erreur sont affichées. « Plus » → « Afficher helixsr.log » montre le journal complet avec un bouton de copie.
- Sur les GPU **RDNA 3 et plus récents**, dans les jeux utilisant la méthode OptiScaler, le README de HelixSR recommande `WaveSize = 64` quand le journal indique wave32. L'outil le détecte et propose « Régler WaveSize = 64 » en un clic.
- L'indicateur GPU en haut affiche la génération de votre GPU (par exemple « AMD RDNA 3 (gfx1100) »).

### 7. Incrustation au lancement d'un jeu

Si l'Assistant HelixSR est ouvert quand un jeu avec HelixSR démarre, une petite carte apparaît en bas à droite pendant environ 10 secondes dès que HelixSR est chargé, avec la version, la méthode et la taille des vagues (une fois par lancement ; les jeux déjà lancés avant l'ouverture de l'outil sont ignorés). Si HelixSR n'est toujours pas chargé au bout de 90 secondes, la carte indique quoi choisir dans le jeu. L'incrustation est une fenêtre X11 (XWayland) séparée qui ne prend jamais le focus et laisse passer les clics. Désactivable avec la case de la barre d'outils. Elle n'apparaît pas en mode Jeu du Steam Deck (gamescope).

### 8. Lancer les jeux, rechercher et filtrer

- Chaque ligne a un bouton « ▶ Lancer » (via `steam://rungameid/<AppID>`) ; il affiche « En cours » pendant que le jeu tourne.
- Recherche par nom de jeu (dans toute langue) ou par App ID. Filtres : jeux pouvant utiliser HelixSR, installé, non installé, mise à jour ou réparation nécessaire, en cours, tous les jeux.

### 9. Douze langues d'interface

台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी. La langue du système est utilisée au premier démarrage ; changez-la en haut à droite (effet immédiat, mémorisé).

### 10. Pensé pour la sécurité

- Rien n'est modifié tant que le dossier HelixSR n'est pas préparé ou que le jeu est lancé.
- Chaque fichier remplacé par HelixSR est conservé (`*.original.dll` ou `HelixSR/backup`), et chaque fichier copié est vérifié octet par octet.
- Un `OptiScaler.ini` existant est sauvegardé et restauré au retrait ; une DLL FSR que vous avez remplacée à la main dans le dossier `HelixSR` du jeu est conservée lors des mises à jour.
- La méthode DLSS et les jeux avec anti-triche exigent une confirmation explicite.

## Compatible avec l'installation de HelixSR

L'Assistant HelixSR écrit le même enregistrement d'installation (`helixsr-install.json`), les mêmes sauvegardes et noms de fichiers que l'installation de HelixSR. Ainsi :

- Les jeux préparés avec `helixsr-setup.sh` apparaissent comme installés dans l'Assistant HelixSR, avec leur méthode, et peuvent y être modifiés, mis à jour ou retirés.
- Les jeux préparés avec l'Assistant HelixSR sont reconnus par l'installation de HelixSR et par `helixsr-uninstall.sh`, qui peuvent les mettre à jour ou les retirer.

## Installer l'Assistant HelixSR

**AppImage (recommandé)** : Python et Qt sont inclus, rien d'autre à installer.

1. Téléchargez `HelixSR_Assistant-<version>-x86_64.AppImage` depuis la page [Releases](https://github.com/mosesmoon/helixsr-assistant/releases).
2. Rendez-le exécutable : clic droit sur le fichier → Propriétés → Permissions, puis activez « Autoriser l'exécution du fichier comme un programme » (le libellé varie selon le gestionnaire de fichiers).
3. Double-cliquez dessus pour ouvrir l'Assistant HelixSR.

Ou dans un terminal :

```bash
chmod +x HelixSR_Assistant-*-x86_64.AppImage
./HelixSR_Assistant-*-x86_64.AppImage
```

S'il ne démarre pas, il manque peut-être FUSE à votre système ; lancez-le alors avec `./HelixSR_Assistant-*-x86_64.AppImage --appimage-extract-and-run`.

**Depuis les sources** : nécessite Python 3.11 ou plus récent et PyQt6 (Arch : `sudo pacman -S python-pyqt6`).

```bash
./helixsr-assistant    # lancer directement
./install.sh           # installer dans ~/.local/share/helixsr-assistant et ajouter une entrée de menu
```

## Limites connues

- **Jeux Steam uniquement.** Pour les jeux d'autres boutiques, utilisez l'installation de HelixSR (glissez-y le dossier du jeu).
- HelixSR ne fonctionne que dans les jeux Direct3D 12. Un jeu listé avec une DLL DLSS ou FSR peut tout de même utiliser Vulkan ou Direct3D 11 ; HelixSR n'y fait alors rien.
- HelixSR évolue très vite. L'Assistant HelixSR nécessite HelixSR 1.8.0 ou plus récent et a été conçu pour l'organisation des versions 1.8.x et 1.9.x ; si une future version de HelixSR change la façon de préparer les jeux, utilisez l'installation de HelixSR jusqu'à la mise à jour de l'Assistant.
- L'incrustation n'apparaît pas en mode Jeu du Steam Deck (gamescope), et les jeux en plein écran exclusif Wayland natif peuvent la masquer.
- En thaï, vietnamien, malais et hindi, les menus contextuels sont en anglais (Qt n'a pas de traduction officielle pour ces langues). Steam n'a pas de noms de jeux en malais ni en hindi : ces deux langues affichent toujours les noms d'origine.

## Où sont stockées les données

| Emplacement | Contenu |
|---|---|
| `~/.config/helixsr-assistant/state.json` | État propre à l'Assistant HelixSR : dossier HelixSR, cache de la liste des jeux, langue de l'interface, réglage de l'incrustation |
| `<jeu>/…/HelixSR/helixsr-install.json`, à côté de la DLL FSR du jeu | Enregistrement d'installation de HelixSR (partagé avec son installation) |
| `<jeu>/…/helixsr.ini` | Réglages de HelixSR pour ce jeu |
| `<jeu>/…/helixsr.log` | Ce que HelixSR a signalé lors du dernier lancement du jeu |

## Licences

L'Assistant HelixSR est un outil indépendant et non officiel. Il n'est ni affilié ni approuvé par l'auteur de HelixSR, NVIDIA, AMD ou le projet OptiScaler, et ne contient aucun de leurs fichiers. HelixSR est gratuit sous la HelixSR Freeware License. Une fois l'installation de HelixSR exécutée, ses DLL contiennent le réseau de NVIDIA : l'Assistant HelixSR se contente de les copier entre des dossiers de votre propre PC. Ne les partagez et ne les téléversez jamais.
