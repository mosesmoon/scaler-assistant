# Assistant Scaler — Guide des fonctionnalités

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · **Français** · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

L'**Assistant Scaler** est un outil de bureau Linux qui vous permet de choisir la mise à l'échelle de chacun de vos jeux Steam — **DLSS 3.7 ([HelixSR](https://github.com/lonewolf0622/HelixSR))**, **FSR 4.1** (Exact ou Lossy de [fsr4-shader-performance-overrides](https://github.com/zgauthier2000/fsr4-shader-performance-overrides), ou celui d'AMD sur RX 9000) ou **FSR 3** — et l'installe, la change, la met à jour, la répare et la retire en un clic. Il indique aussi si elle tourne vraiment pendant que vous jouez.

## Pour qui

Mettre à la main une meilleure mise à l'échelle dans un jeu sous Linux, c'est :

1. Trouver les mises à l'échelle que le jeu embarque (DLSS, XeSS, FSR 2, FSR 3.1), son API graphique et l'emplacement de son `.exe` principal.
2. Placer OptiScaler à côté du `.exe` sous un nom de fichier que le jeu accepte, avec les DLL FidelityFX nécessaires, et modifier `OptiScaler.ini` pour la mise à l'échelle voulue.
3. Ajouter `WINEDLLOVERRIDES` aux options de lancement Steam quand ce nom de fichier l'exige — sans casser ce qui s'y trouve.
4. Télécharger la bonne DLL FSR 4.1 pour votre GPU, ou configurer HelixSR comme l'indique son README.
5. Tout refaire après chaque mise à jour, et encore quand une mise à jour du jeu écrase vos fichiers.

L'Assistant Scaler fait tout cela depuis une seule fenêtre et garde tout ce qu'il remplace : la suppression remet le jeu exactement comme avant.

## Les choix pour chaque jeu

L'API graphique et les mises à l'échelle du jeu déterminent ce qui est proposé. Le jeu doit déjà embarquer au moins une mise à l'échelle (DLSS, XeSS, FSR 2 ou FSR 3.1) : c'est elle qu'OptiScaler et HelixSR reprennent.

| Choix | Le jeu doit avoir | Ce qui est placé dans le dossier du jeu | À choisir dans le jeu |
|---|---|---|---|
| **DLSS 3.7 (HelixSR) · méthode FSR** | Direct3D 12, FSR 3.1 | La DLL FSR 3.1 du jeu est remplacée par HelixSR (le fichier du jeu est gardé en `*.original.dll`) | AMD FSR |
| **DLSS 3.7 (HelixSR) · méthode OptiScaler** | Direct3D 12, DLSS, XeSS ou FSR 2 | OptiScaler à côté du `.exe`, pointé vers un dossier `HelixSR` | DLSS |
| **DLSS 3.7 (HelixSR) · méthode DLSS** (expérimentale) | Direct3D 12, DLSS | Le chargeur DLSS de HelixSR (`dxgi.dll`) et HelixSR en tant que `nvngx.dll` | DLSS |
| **FSR 4.1 Exact** | l'une des quatre mises à l'échelle | OptiScaler à côté du `.exe` ; les DLL FidelityFX et la DLL FSR 4.1 Exact dans un dossier `ScalerAssistant` | DLSS, FSR ou XeSS |
| **FSR 4.1 Lossy** | idem | idem, avec la DLL FSR 4.1 Lossy | DLSS, FSR ou XeSS |
| **FSR 4.1 Lossy2** | idem | idem, avec la DLL FSR 4.1 Lossy2 | DLSS, FSR ou XeSS |
| **FSR 4.1 (AMD)** — à la place d'Exact / Lossy sur RX 9000 (RDNA 4) | idem | idem, avec la DLL FSR 4.1 d'AMD | DLSS, FSR ou XeSS |
| **FSR 3** | idem | idem ; OptiScaler utilise FSR 3.1.5 | DLSS, FSR ou XeSS |

- **Exact** donne l'image du FSR 4.1 d'AMD à l'octet près, avec des shaders plus rapides. **Lossy** est encore plus rapide et modifie légèrement l'image ; l'Assistant Scaler affiche une fois son `WARNING.txt` avant la première utilisation. Dans le doute, prenez Exact.
- **Lossy2** est Lossy avec six des douze couches du réseau réentraînées : le feuillage qui bouge se rapproche de l'image d'AMD et il y a moins de pixels lucioles, mais il suit plus lentement les éclaircissements et il est identique à Lossy en Ultra Performance. Il est proposé à côté de Lossy pour les comparer et affiche une fois son propre `WARNING.txt`.
- HelixSR ne fonctionne que dans les jeux **Direct3D 12** : DLSS 3.7 n'est proposé que là. FSR 4.1 et FSR 3 fonctionnent aussi dans les jeux **Direct3D 11 et Vulkan** : FSR 3 en natif, FSR 4.1 via le chemin Direct3D 12 d'OptiScaler (moins testé que les jeux Direct3D 12).
- Cliquez sur **« Choisir la mise à l'échelle »** dans la ligne du jeu (ou **« Mise à l'échelle »** une fois installée) : DLSS 3.7 (HelixSR) ouvre un sous-menu avec ses méthodes ; le choix actuel est coché. Changer retire d'abord le choix actuel et remet tout en place.

## Avant de commencer

- **FSR 4.1 et FSR 3** ne demandent rien d'autre : la première fois, l'Assistant Scaler propose de télécharger OptiScaler et les DLL FSR 4.1 pour votre GPU (voir « Téléchargements »).
- **DLSS 3.7** nécessite HelixSR, que l'Assistant Scaler n'inclut pas. Téléchargez HelixSR 1.8.0 ou plus récent depuis ses [GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases), extrayez-le dans un dossier que vous gardez et lancez-y une fois `./helixsr-setup.sh` (il construit le réseau de HelixSR sur votre PC ; quand il pose des questions sur les jeux, vous pouvez répondre `n`). La pastille **HelixSR** en haut explique tout cela ; un dossier HelixSR configuré dans votre dossier personnel, Téléchargements, Bureau ou Games est trouvé automatiquement.
  Plus simple : appuyez sur **Télécharger et construire HelixSR** dans cette fenêtre (HelixSR 2.0 ou plus récent) ; Scaler Assistant fait tout cela pour vous, sans terminal.
- Les jeux tournent via **Proton**. HelixSR est conçu pour les GPU AMD (RDNA 1 et plus récents). FSR 4.1 Exact / Lossy sont faits pour les Radeon RX 7000 / RX 6000 et les puces graphiques Radeon intégrées (Steam Deck compris) ; les autres GPU devraient les faire tourner, mais leur auteur ne les a pas testés. FSR 4.1 ne fonctionne pas sur les GPU Radeon RX 5000 (RDNA 1) (chaque version n'affiche qu'une image noire) : l'Assistant Scaler le grise donc sur ces cartes ; FSR 3 et DLSS 3.7 (HelixSR) restent disponibles.

## Fonctionnalités

### 1. Analyse vos jeux Steam

- Toutes les bibliothèques Steam sont analysées au premier démarrage (y compris sur d'autres disques). Cliquez sur « ⟳ Réanalyser les jeux Steam » après avoir installé des jeux.
- Pour chaque jeu : les DLL de mise à l'échelle, le dossier du `.exe` principal (d'après les informations de lancement de Steam ; lanceurs et `*-Shipping.exe` d'Unreal gérés), l'**API graphique** (lue dans la table d'import du `.exe` : DX12, DX11 ou Vulkan) et la présence d'un **anti-triche** (Easy Anti-Cheat, BattlEye).
- Les noms suivent la langue de l'interface (noms localisés de Steam). Les jeux pouvant être mis à l'échelle viennent en premier.

### 2. Un nom de fichier d'OptiScaler qui fonctionne dans le jeu

Le jeu charge OptiScaler comme une DLL système à côté de son `.exe`. Le nom est choisi ainsi :

1. celui que vous avez choisi pour le jeu (« Plus » → « Nom de fichier d'OptiScaler… »),
2. le nom d'un OptiScaler déjà présent,
3. le nom que donne la [liste de compatibilité d'OptiScaler](https://github.com/optiscaler/OptiScaler/wiki) pour le jeu (par exemple `d3d12.dll` ou `winmm.dll`),
4. `winmm.dll` pour les jeux Vulkan,
5. un autre nom libre (`winmm.dll`, `version.dll`, …) quand le jeu ou un autre mod (ReShade par exemple) a déjà un `dxgi.dll`, ou quand vos options de lancement fixent ce nom sur la version intégrée,
6. sinon `dxgi.dll`.

Un fichier déjà présent n'est jamais écrasé : il va dans `ScalerAssistant/backup` (`HelixSR/backup` pour DLSS 3.7) et revient à la suppression.

### 3. Options de lancement Steam : seulement le nécessaire, les vôtres restent telles quelles

Sous Proton, `dxgi.dll` et `d3d12.dll` se chargent sans rien d'autre. Tout autre nom nécessite `WINEDLLOVERRIDES="<nom>=n,b"` dans les options de lancement, que l'Assistant Scaler ajoute pour vous :

- **Seule cette entrée est insérée.** Si vous avez déjà `WINEDLLOVERRIDES`, `;winmm=n,b` est ajouté dedans ; sinon `WINEDLLOVERRIDES="winmm=n,b"` est placé devant (avec `%command%` s'il manquait). Rien d'autre ne change. Exemple : `-dx12 %command%` devient `WINEDLLOVERRIDES="winmm=n,b" -dx12 %command%`.
- **Seule cette entrée est retirée** quand OptiScaler est supprimé ou renommé. Si vous n'avez pas modifié les options entre-temps, elles redeviennent exactement ce qu'elles étaient ; sinon seul le texte inséré est retiré et vos modifications restent.
- Une entrée que vous aviez déjà pour ce nom n'est pas touchée et n'est pas retirée plus tard. Si vos options règlent ce nom sur la version intégrée de Wine, l'Assistant Scaler prend un autre nom plutôt que de modifier votre réglage.
- Si l'entrée disparaît plus tard, le jeu affiche « Option de lancement manquante » et « Réparer » la rajoute.
- Si Steam est ouvert, les options sont changées via Steam lui-même quand son port de débogage est disponible (comme pour Decky Loader). Sinon l'Assistant Scaler propose de fermer Steam, d'écrire la modification et de relancer Steam — avant de toucher au moindre fichier du jeu.

### 4. Téléchargements (FSR 4.1 et FSR 3)

Cliquez sur la pastille **OptiScaler** en haut (ou celle du GPU) :

- **OptiScaler 0.9.4** (avec les DLL FidelityFX d'AMD : FSR 3 et le FSR 4.1 d'AMD, plus fakenvapi) et **FSR 4.1 Exact / Lossy / Lossy2** dans la version pour votre GPU : cartes RX 7000, cartes RX 6000, puce RDNA 3 intégrée au processeur (aussi GeForce, Intel Arc et autres GPU), ou Steam Deck et puce RDNA 2 intégrée au processeur. Chaque version fonctionne sur tous ; celle de votre GPU est la plus rapide. Si un jeu plante avec Exact, choisissez une version pour puce intégrée.
- Rien n'est téléchargé sans votre accord. Chaque téléchargement est une version fixe vérifiée par sa taille et son SHA-256 avant d'être extrait ; seuls les fichiers utiles aux jeux sont gardés, dans `~/.local/share/scaler-assistant/components/`.
- **Version de FSR 4.1** : automatique selon votre GPU (RX 9000 / RDNA 4 → FSR 4.1 d'AMD, puce intégrée et Steam Deck → version intégrée, autres GPU → version cartes graphiques), ou choisie à la main. Les DLL modifiées ne sont jamais utilisées sur RDNA 4. Sur les autres GPU, OptiScaler est réglé sur le modèle INT8 de FSR 4.
- « Supprimer les téléchargements » les efface ; les jeux gardent leurs propres copies.

### 5. Ce qui change dans OptiScaler.ini

Seulement les lignes nécessaires, dans leur propre section ; toutes les autres lignes et commentaires sont conservés :

| Clé | FSR 4.1 | FSR 3 |
|---|---|---|
| `Dx12Upscaler` | `fsr31` | `fsr31` |
| `Dx11Upscaler`, `VulkanUpscaler` | `fsr31_12` (via Direct3D 12) | `fsr31` (natif) |
| `UpscalerIndex` | `0` (FSR 4) | `1` (FSR 3.1.5) |
| `Fsr4Update` | `true` | `false` |
| `Fsr4ForceEnableInt8` | `true` avant RDNA 4 | `auto` |
| `FfxDx12Path`, `FfxDx12SRPath`, `FfxDx12FGPath`, `FfxVkPath` | les DLL du dossier `ScalerAssistant` du jeu | idem |

Un `OptiScaler.ini` déjà présent est d'abord sauvegardé, puis remis en place à la suppression.

### 6. Changer, mettre à jour, réparer, retirer

- **Changer** depuis le menu de mise à l'échelle : le choix actuel est retiré d'abord, puis le nouveau installé. Entre FSR 4.1 Exact, Lossy et FSR 3, seuls la DLL FSR et `OptiScaler.ini` changent.
- **Mettre à jour** : un jeu affiche « ↑ HelixSR … disponible » quand votre dossier HelixSR a une version plus récente, ou « ↑ Téléchargement plus récent disponible » quand un téléchargement OptiScaler / FSR 4.1 plus récent (ou une autre version de FSR 4.1) s'applique. « ↑ Tout mettre à jour » traite tous les jeux.
- **Réparer** : une mise à jour du jeu ou « Vérifier l'intégrité des fichiers du jeu » peut remettre les fichiers du jeu. Le jeu indique alors ce qui s'est passé et « Réparer » remet la mise à l'échelle, en gardant les nouveaux fichiers du jeu comme sauvegarde.
- **Retirer** remet chaque fichier remplacé ou déplacé et retire l'entrée des options de lancement.

### 7. Réglages de HelixSR sans éditer de fichier

Pour DLSS 3.7, « ⚙ Réglages » modifie le `helixsr.ini` du jeu par un formulaire (netteté, réseau int8, dernière passe en Ultra Performance, taille des vagues). « Par défaut » omet la ligne ; les autres lignes et commentaires sont conservés.

### 8. État en direct et incrustation

- Les jeux Steam en cours sont vérifiés toutes les 3 secondes : `/proc/<pid>/maps` indique si le jeu a **vraiment chargé** HelixSR ou la DLL FSR (et OptiScaler ou le chargeur DLSS). Rien n'est chargé tant que le jeu n'utilise pas la mise à l'échelle : « pas encore chargé » vous dit donc quoi choisir dans le jeu.
- Pour HelixSR, le `helixsr.log` de la session indique la taille des vagues et les erreurs ; sur RDNA 3 et plus récents avec la méthode OptiScaler, « Régler WaveSize = 64 » est proposé quand le journal indique wave32.
- Le panneau de détails d'un jeu (le bouton ⌄ de sa carte) propose « Voir …log » pour `helixsr.log` ou `OptiScaler.log`, le dossier du jeu, le nom de fichier d'OptiScaler et, pour DLSS 3.7, « ⚙ Réglages ».
- Au lancement d'un jeu, une petite carte en bas à droite affiche le résultat environ 10 secondes (ou un conseil après 90 secondes). C'est une fenêtre X11 séparée qui ne prend jamais le focus ; désactivable via l'interrupteur de la barre d'outils.

### 9. Lancer, chercher, filtrer, langues

- « ▶ Lancer » démarre le jeu via Steam. Recherche par nom (toute langue) ou App ID ; filtres : jeux pouvant être mis à l'échelle, mise à l'échelle installée, pas encore de mise à l'échelle, mise à jour ou réparation nécessaire, en cours, tous les jeux.
- 12 langues d'interface : 台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी.

### 10. Conçu pour la sécurité

- Rien ne change pendant que le jeu tourne ; téléchargements et dossier HelixSR sont vérifiés avant de toucher à un fichier.
- Chaque fichier remplacé est conservé, chaque copie vérifiée octet par octet, et les options de lancement ne changent que de l'entrée décrite plus haut.
- La méthode DLSS, FSR 4.1 Lossy et les jeux avec anti-triche demandent d'abord confirmation. N'utilisez jamais de mise à l'échelle modifiée en ligne : l'anti-triche peut y voir une manipulation.

### 11. Apparence

- Dans le style de MAKO Assistant (« Liquid Glass ») : une carte par jeu avec sa jaquette Steam, une pastille d'état, ce que le jeu propose et, pendant qu'il tourne, ce qui est réellement chargé. Le bouton ⌄ ouvre les détails (API graphique, upscalers, dossier du `.exe`, nom d'OptiScaler, options de lancement) et les actions moins courantes.
- Les boutons sont en cristal clair en relief : une teinte légère avec une bordure fine, un reflet courbe sur la moitié haute, un éclat le long du bord inférieur et une ombre douce dessous — uniquement des couches translucides unies, sans dégradé. Les boutons des interrupteurs ressortent de la même façon ; le thème choisi est un cristal en relief dans une piste creusée. Turquoise installe, bleu change, ambre met à jour, rouge supprime.
- Thème sombre, clair ou automatique (suit le bureau). Le journal d'activité est le tiroir en bas de la fenêtre.

## HelixSR 2.0 et le GPU

- **Télécharger et construire HelixSR en une étape** : « Télécharger et construire HelixSR » (dans la fenêtre HelixSR et dans le plugin Steam Deck) télécharge le dernier HelixSR (2.0 ou plus récent) depuis ses versions GitHub, vérifié par SHA-256, dans `~/.local/share/scaler-assistant/helixsr`, puis le construit sur ce PC avec le programme de construction de HelixSR (`setup/helixsr_setup.py`, lancé tel quel) — comme le fait l'application de HelixSR, donc sans terminal ni étape des jeux. Il fournit ce dont la construction a besoin : un Python avec numpy (un Python 3.14 portable quand celui du système ne sait pas décompresser le paquet zstd de NVIDIA, pour que la génération d'images n'exige pas `zstd`) et le DirectX Shader Compiler de Microsoft, lancé via Proton de Steam ou Wine. Les fichiers de NVIDIA ne sont téléchargés qu'après votre accord dans l'application ; le résultat reste sur votre PC. Dans Flatpak, la construction s'exécute sur l'hôte. Relancer ne construit que ce qui manque ; une version plus récente remplace celle téléchargée avant.
- **HelixSR 2.0 et plus récent** placent la DLL construite dans `HelixSR-fsrfg` et proposent deux méthodes : **HelixSR Scaler** (l'OptiScaler propre à HelixSR à côté du `.exe` : choisir DLSS dans le jeu ; aussi les jeux DX11 et Vulkan) et la **méthode FSR** (FSR drop-in). L'Assistant Scaler installe les deux via l'installateur de votre dossier HelixSR (`setup/helixsr_bridge.py`, celui qu'utilise l'application d'HelixSR), si bien que le setup d'HelixSR, son application et l'Assistant Scaler reconnaissent, mettent à jour et retirent les installations des autres. L'Assistant Scaler choisit toujours le nom de fichier et ajoute l'option de lancement si nécessaire. Les jeux configurés avec une méthode antérieure passent à HelixSR Scaler lors de la mise à jour. Les dossiers HelixSR 1.8 / 1.9 gardent leurs trois méthodes.
- **Génération d'images HelixSR** (HelixSR 2.0) : dans les jeux DirectX 12 dotés de DLSS Frame Generation (le `sl.dlss_g.dll` de Streamline), un jeu avec HelixSR Scaler reçoit un interrupteur « Génération d'images HelixSR » sur sa carte (et dans le plugin Steam Deck). Il passe par l'installateur de HelixSR (`scaler-fg`), qui ne modifie que le choix `[FrameGen]` d'OptiScaler.ini ; activez ensuite DLSS Frame Generation dans le jeu. Il faut la génération d'images créée par `./helixsr-setup.sh` (qui télécharge les fichiers DLSS Frame Generation de NVIDIA) ; d'ici là l'interrupteur est grisé avec la raison. Une nouvelle installation la laisse désactivée ; une mise à jour ou un nouveau nom de fichier OptiScaler conserve l'état. Les autres jeux DX12 peuvent toujours choisir la génération d'images AMD FSR ou XeSS dans le menu de HelixSR Scaler (Inser) ; les jeux DX11 / Vulkan et la voie FSR n'ont que l'upscaling.
- **HelixSR 3.0** : la DLL construite est `HelixSR/helixsr.dll` (l'upscaler DLSS de HelixSR Scaler, « HLX DLSS »), et la voie FSR installe **HLX FSR 4**, le pipeline FSR 4 propre à HelixSR, que le setup de HelixSR construit à partir du fichier pilote FSR 4 d'AMD (il télécharge environ 420 Mo du paquet de pilotes d'AMD ; « Télécharger et construire HelixSR » le demande d'abord et fournit aussi le second compilateur de shaders, DXC 1.9.2609). L'Assistant Scaler installe, met à jour, change et retire les deux voies via l'installateur de la version, comme avec 2.0 ; les jeux configurés avec 2.0 passent de `HelixSR-fsrfg` à `HelixSR` lors de la mise à jour. HelixSR 3.0 n'a pas de génération d'images : l'interrupteur ci-dessus n'apparaît donc pas avec lui ; les générations d'images AMD FSR et XeSS restent dans le menu de HelixSR Scaler.
- **Versions antérieures d'HelixSR** : 1.8.x propose les trois méthodes (FSR, OptiScaler, DLSS). HelixSR 1.9.0 – 1.9.3 ne contiennent que les fichiers de la méthode FSR, donc les méthodes OptiScaler et DLSS y sont grisées (« demande HelixSR 1.8 ou 2.0 ») ; les jeux sans FSR 3.1 demandent HelixSR 2.0 (HelixSR Scaler). Les versions antérieures à 1.8.0 ne sont pas prises en charge.
- **Méthode DLSS uniquement avec une GeForce** : avec un GPU AMD ou Intel, les jeux ne proposent pas DLSS, donc la méthode DLSS (HelixSR 1.x) est grisée avec la raison.
- **FSR 4.1 Lossy recommandé** sur les graphismes intégrés (Steam Deck, ROG Ally Z1 / Z2, Ryzen AI MAX) et les GPU Intel : marqué « ★ Recommandé » uniquement parmi les choix FSR 4.1.

## Fonctionne avec l'installation propre à HelixSR

Pour DLSS 3.7, l'Assistant Scaler écrit le même enregistrement d'installation (`helixsr-install.json`), les mêmes sauvegardes et noms de fichiers que l'installation de HelixSR : `helixsr-setup.sh` / `helixsr-uninstall.sh` et l'Assistant Scaler reconnaissent les jeux l'un de l'autre. L'installation de HelixSR prend la DLL FSR du dossier `ScalerAssistant` d'un jeu pour la DLL FSR 3.1 du jeu et peut la remplacer par HelixSR ; l'Assistant Scaler signale alors le jeu comme à réparer et « Réparer » retire HelixSR. Pour utiliser DLSS 3.7 dans un tel jeu, choisissez-le dans l'Assistant Scaler.

## Plugin Steam Deck (Decky Loader)

Le même programme pour le mode Jeu, en plugin [Decky Loader](https://decky.xyz) dans le menu d'accès rapide.

- **Jeux** : les jeux qui peuvent être upscalés, ceux en cours d'abord, chacun avec sa pastille d'état et, pendant qu'il tourne, ce qui est réellement chargé. Choisissez un jeu pour sélectionner DLSS 3.7 (HelixSR, chaque méthode), FSR 4.1 Exact / Lossy ou FSR 3, ou pour le mettre à jour, le réparer, le retirer, changer le nom de fichier d'OptiScaler ou lire son journal. Les mêmes questions viennent d'abord que dans l'application de bureau : téléchargements, avertissement Lossy, méthode DLSS et anti-triche.
- **Configuration** : le dossier HelixSR (sélecteur de fichiers), les téléchargements et la version FSR 4.1 (le Steam Deck reçoit la version pour graphismes intégrés), une notification au lancement d'un jeu (indique si l'upscaler est chargé) et la langue (par défaut celle de Steam).
- Il partage `state.json`, les téléchargements et les entrées d'options de lancement avec l'application de bureau : les jeux configurés dans l'un apparaissent dans l'autre. Les options de lancement sont écrites en direct via Steam.
- Absents du plugin : le formulaire des réglages HelixSR (utilisez l'application de bureau) et le `helixsr-setup.sh` d'HelixSR, à lancer une fois en mode Bureau.
- Dans le plugin, **Télécharger et construire HelixSR** télécharge et construit HelixSR 2.0 ou plus récent aussi en mode Jeu (quelques minutes).

Installation : installez Decky Loader sur le Steam Deck, téléchargez `Scaler_Assistant-Decky-<version>.zip` depuis la page [Releases](https://github.com/mosesmoon/scaler-assistant/releases), puis dans les réglages de Decky → Développeur (activez d'abord le mode développeur dans Général) → « Install Plugin from ZIP File ».

## Installer l'Assistant Scaler

**AppImage (recommandé)** : Python, Qt et 7-Zip sont inclus.

1. Téléchargez `Scaler_Assistant-<version>-x86_64.AppImage` depuis la page [Releases](https://github.com/mosesmoon/scaler-assistant/releases).
2. Rendez-le exécutable : clic droit → Propriétés → Permissions → « Autoriser l'exécution du fichier comme un programme » (le libellé varie selon le gestionnaire de fichiers).
3. Double-cliquez dessus.

```bash
chmod +x Scaler_Assistant-*-x86_64.AppImage
./Scaler_Assistant-*-x86_64.AppImage
```

S'il ne démarre pas, il manque peut-être FUSE ; lancez-le avec `--appimage-extract-and-run`.

**Installateur unique (.bin)** : `Scaler_Assistant-<version>-x86_64.bin` installe la même application intégrée pour votre utilisateur seulement (sans root ni FUSE) dans `~/.local/opt/scaler-assistant`, avec la commande `scaler-assistant` et une entrée de menu. **Flatpak** : `Scaler_Assistant-<version>-x86_64.flatpak` est un paquet en un seul fichier sur le runtime Freedesktop 25.08 (téléchargé depuis Flathub à l'installation). Il peut lire votre dossier personnel et d'autres disques (cartes SD sous `/run/media`) et voit les processus de Steam et des jeux via `flatpak-spawn --host`.

```bash
sh Scaler_Assistant-*-x86_64.bin                # install / installer
sh Scaler_Assistant-*-x86_64.bin --uninstall    # remove / retirer
flatpak install --user Scaler_Assistant-*-x86_64.flatpak
flatpak run io.github.mosesmoon.ScalerAssistant
```

**Depuis les sources** : Python 3.11+ et PyQt6 (Arch : `sudo pacman -S python-pyqt6`), plus 7-Zip ou bsdtar pour extraire OptiScaler (`sudo pacman -S 7zip`).

```bash
./scaler-assistant     # lancer directement
./install.sh           # installer dans ~/.local/share/scaler-assistant et ajouter une entrée de menu
```

## Limites connues

- **Jeux Steam uniquement.** Les méthodes FSR 4.1 / FSR 3 ont été vérifiées fichier par fichier avec OptiScaler 0.9.4 ; chaque jeu se comporte différemment : en cas de souci, consultez la liste de compatibilité d'OptiScaler ou choisissez un autre nom de fichier pour OptiScaler.
- FSR 4.1 dans les jeux Direct3D 11 et Vulkan passe par le chemin Direct3D 12 d'OptiScaler et est moins testé.
- HelixSR évolue vite. L'Assistant Scaler nécessite HelixSR 1.8.0 ou plus récent et suit l'organisation 1.8.x / 1.9.x / 2.0.x / 3.0.x / 3.1.x.
- L'incrustation n'apparaît pas en mode Jeu du Steam Deck (gamescope). Le plugin Decky affiche à la place une notification Steam.
- En thaï, vietnamien, malais et hindi, les menus contextuels sont en anglais (Qt n'a pas de traduction officielle). Steam n'a pas de noms de jeux en malais ni en hindi.

## Où sont stockées les données

| Emplacement | Contenu |
|---|---|
| `~/.config/scaler-assistant/state.json` | État de l'Assistant Scaler : dossier HelixSR, liste des jeux, langue, version de FSR 4.1, noms d'OptiScaler choisis, entrées ajoutées aux options de lancement (repris une fois de l'Assistant HelixSR) |
| `~/.local/share/scaler-assistant/components/` | Les fichiers OptiScaler et FSR 4.1 téléchargés |
| `~/homebrew/plugins/scaler-assistant/` | Le plugin Decky sur le Steam Deck (même état et mêmes téléchargements que ci-dessus) |
| `<jeu>/…/ScalerAssistant/` | FSR 4.1 / FSR 3 : DLL FidelityFX, `scaler-install.json`, `backup/` |
| `<jeu>/…/HelixSR/helixsr-install.json`, à côté de la DLL FSR du jeu | DLSS 3.7 : enregistrement d'installation de HelixSR (partagé avec son installation) |
| `<jeu>/…/helixsr.ini`, `helixsr.log`, `OptiScaler.ini`, `OptiScaler.log` | Réglages et journaux |

## Licences

L'Assistant Scaler est un outil indépendant et non officiel, sans lien avec l'auteur de HelixSR, NVIDIA, AMD, le projet OptiScaler ou le projet fsr4-shader-performance-overrides, ni approuvé par eux, et il ne contient aucun de leurs fichiers. À votre demande, il télécharge OptiScaler (GPL-3.0 ; fakenvapi MIT ; DLL FidelityFX d'AMD sous licence AMD) et les DLL FSR 4.1 (GPL-2.0-or-later, DLL AMD modifiées avec la mention d'AMD) depuis leurs GitHub Releases. L'AppImage contient le `7zzs` de 7-Zip (GNU LGPL avec restriction unRAR, BSD ; licence incluse). HelixSR est gratuit sous la HelixSR Freeware License ; après son installation, ses DLL contiennent le réseau de NVIDIA : l'Assistant Scaler ne les copie qu'entre des dossiers de votre propre PC. Ne les partagez ni ne les mettez en ligne. Le plugin Decky inclut le même `7zzs`.
