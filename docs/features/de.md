# Scaler-Assistent — Funktionsübersicht

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · **Deutsch** · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

Der **Scaler-Assistent** ist ein Linux-Desktopwerkzeug, mit dem du für jedes Steam-Spiel den Upscaler wählst — **DLSS 3.7 ([HelixSR](https://github.com/lonewolf0622/HelixSR))**, **FSR 4.1** (Exact oder Lossy aus [fsr4-shader-performance-overrides](https://github.com/zgauthier2000/fsr4-shader-performance-overrides), auf RX 9000 AMDs eigenes) oder **FSR 3** — und ihn mit einem Klick installierst, wechselst, aktualisierst, reparierst und entfernst. Beim Spielen zeigt er, ob der Upscaler wirklich läuft.

## Für wen

Einen besseren Upscaler unter Linux von Hand in ein Spiel zu bringen heißt:

1. Herausfinden, welche Upscaler das Spiel mitbringt (DLSS, XeSS, FSR 2, FSR 3.1), welche Grafik-API es nutzt und wo seine Haupt-`.exe` liegt.
2. OptiScaler unter einem Dateinamen, den das Spiel annimmt, neben die `.exe` legen, die nötigen FidelityFX-DLLs dazu, und `OptiScaler.ini` für den gewünschten Upscaler bearbeiten.
3. `WINEDLLOVERRIDES` in die Steam-Startoptionen eintragen, wenn der Dateiname das braucht — ohne Vorhandenes zu zerstören.
4. Die passende FSR-4.1-DLL für die GPU herunterladen oder HelixSR nach seiner README einrichten.
5. Alles nach jedem Update wiederholen, und wieder, wenn ein Spiel-Update die Dateien überschreibt.

Der Scaler-Assistent erledigt das in einem Fenster und behält alles, was er ersetzt; beim Entfernen ist das Spiel wieder genau wie vorher.

## Die Möglichkeiten pro Spiel

Grafik-API und Upscaler des Spiels bestimmen, was angeboten wird. Das Spiel muss mindestens einen Upscaler mitbringen (DLSS, XeSS, FSR 2 oder FSR 3.1): Den übernehmen OptiScaler und HelixSR.

| Wahl | Das Spiel braucht | Was in den Spielordner kommt | Im Spiel wählen |
|---|---|---|---|
| **DLSS 3.7 (HelixSR) · FSR-Weg** | Direct3D 12, FSR 3.1 | Die FSR-3.1-DLL des Spiels wird durch HelixSR ersetzt (die Datei des Spiels bleibt als `*.original.dll`) | AMD FSR |
| **DLSS 3.7 (HelixSR) · OptiScaler-Weg** | Direct3D 12, DLSS, XeSS oder FSR 2 | OptiScaler neben der `.exe`, auf einen `HelixSR`-Ordner gerichtet | DLSS |
| **DLSS 3.7 (HelixSR) · DLSS-Weg** (experimentell) | Direct3D 12, DLSS | HelixSRs DLSS-Lader (`dxgi.dll`) und HelixSR als `nvngx.dll` | DLSS |
| **FSR 4.1 Exact** | einer der vier Upscaler | OptiScaler neben der `.exe`; FidelityFX-DLLs und die Exact-FSR-4.1-DLL in einem Ordner `ScalerAssistant` | DLSS, FSR oder XeSS |
| **FSR 4.1 Lossy** | dasselbe | dasselbe, mit der Lossy-FSR-4.1-DLL | DLSS, FSR oder XeSS |
| **FSR 4.1.2 Lite / Lite Lossy** | dasselbe | dasselbe, mit der 4.1.2l-exact / 4.1.2l-lossy-FSR-4.1-DLL | DLSS, FSR oder XeSS |
| **FSR 4.1 (AMD)** — statt Exact / Lossy auf RX 9000 (RDNA 4) | dasselbe | dasselbe, mit AMDs eigener FSR-4.1-DLL | DLSS, FSR oder XeSS |
| **FSR 3** | dasselbe | dasselbe; OptiScaler nutzt FSR 3.1.5 | DLSS, FSR oder XeSS |

- **Exact** liefert AMDs FSR-4.1-Bild Byte für Byte, mit schnelleren Shadern. **Lossy** ist noch schneller und verändert das Bild leicht; vor der ersten Nutzung zeigt der Scaler-Assistent einmal seine `WARNING.txt`. Im Zweifel nimm Exact.
- **Lossy** ist seit den DLLs von dll-2026-10-29 das frühere Lossy2, weiter trainiert (das ältere Lossy entfällt): viel weniger dunkle Punkte im Laub, aber es folgt Aufhellungen langsamer. **Lite** und **Lite Lossy** verwenden AMDs kleineres FSR-4.1.2-Lite-Netz (wohl das, was AMDs Treiber für integrierte Grafik nutzt): Lite liefert Lites Bild Byte für Byte und ist etwas schneller als AMDs Lite; Lite Lossy führt es nur jedes zweite Bild aus und ist der schnellste Build, mit einem Bild nahe an Lite. Lite ist bei Standbildern und manchen Bewegungen etwas ungenauer als volles FSR 4, bei anderen besser. Lossy und Lite Lossy zeigen jeweils einmal ihre eigene `WARNING.txt`. Mit Lossy2 eingerichtete Spiele erscheinen als veraltet und werden auf Lossy aktualisiert.
- HelixSR funktioniert nur in **Direct3D-12**-Spielen, daher gibt es DLSS 3.7 nur dort. FSR 4.1 und FSR 3 funktionieren auch in **Direct3D-11- und Vulkan**-Spielen: FSR 3 nativ, FSR 4.1 über OptiScalers Direct3D-12-Pfad (weniger getestet als Direct3D-12-Spiele).
- Klicke in der Zeile des Spiels auf **„Upscaler wählen“** (oder **„Upscaler“**, sobald einer installiert ist): DLSS 3.7 (HelixSR) öffnet ein Untermenü mit seinen Wegen; die aktuelle Wahl ist abgehakt. Beim Wechsel wird zuerst die aktuelle entfernt und alles zurückgestellt.

## Bevor du anfängst

- **FSR 4.1 und FSR 3** brauchen nichts weiter: Beim ersten Mal fragt der Scaler-Assistent, ob er OptiScaler und die FSR-4.1-DLLs für deine GPU herunterladen soll (siehe „Downloads“).
- **DLSS 3.7** braucht HelixSR, das der Scaler-Assistent nicht enthält. Lade HelixSR 1.8.0 oder neuer von den [GitHub-Releases](https://github.com/lonewolf0622/HelixSR/releases), entpacke es in einen Ordner, den du behältst, und führe dort einmal `./helixsr-setup.sh` aus (es baut HelixSRs Netz auf deinem PC; Fragen zu Spielen kannst du mit `n` beantworten). Ein Klick auf die **HelixSR**-Plakette oben zeigt das; einen eingerichteten HelixSR-Ordner in Home, Downloads, Desktop oder Games findet der Scaler-Assistent selbst.
  Einfacher: Im selben Fenster **HelixSR herunterladen und erstellen** drücken (HelixSR 2.0 oder neuer); Scaler Assistant erledigt das alles ohne Terminal.
- Spiele laufen über **Proton**. HelixSR ist für AMD-GPUs ab RDNA 1 gemacht. FSR 4.1 Exact / Lossy sind für Radeon RX 7000 / RX 6000 und integrierte Radeon-Grafik (auch Steam Deck) gemacht; andere GPUs sollten sie ausführen, sind vom Autor aber ungetestet. FSR 4.1 funktioniert nicht auf Radeon-RX-5000-GPUs (RDNA 1) (jede Version zeigt nur ein schwarzes Bild), daher graut Scaler-Assistent es dort aus; FSR 3 und DLSS 3.7 (HelixSR) bleiben verfügbar.

## Funktionen

### 1. Liest deine Steam-Spiele ein

- Beim ersten Start werden alle Steam-Bibliotheken durchsucht (auch auf anderen Laufwerken). Nach neuen Spielen „⟳ Steam-Spiele neu einlesen“ klicken.
- Pro Spiel: die mitgelieferten Upscaler-DLLs, der Ordner der Haupt-`.exe` (aus Steams Startinformationen; Launcher und Unreals `*-Shipping.exe` werden berücksichtigt), die **Grafik-API** (aus der Importtabelle der `.exe`: DX12, DX11 oder Vulkan) und ob es einen **Anti-Cheat** hat (Easy Anti-Cheat, BattlEye).
- Spielnamen folgen der Oberflächensprache (Steams lokalisierte Namen). Hochskalierbare Spiele stehen oben.

### 2. Ein Dateiname für OptiScaler, der im Spiel funktioniert

Das Spiel lädt OptiScaler als System-DLL neben seiner `.exe`. Der Name wird so gewählt:

1. ein Name, den du für das Spiel gewählt hast („Mehr“ → „Dateiname von OptiScaler…“),
2. der Name eines OptiScaler, der schon da ist,
3. der Name, den [OptiScalers Kompatibilitätsliste](https://github.com/optiscaler/OptiScaler/wiki) für das Spiel nennt (zum Beispiel `d3d12.dll` oder `winmm.dll`),
4. `winmm.dll` für Vulkan-Spiele,
5. ein anderer freier Name (`winmm.dll`, `version.dll`, …), wenn das Spiel oder eine andere Mod (etwa ReShade) schon eine `dxgi.dll` hat oder deine Startoptionen diesen Namen auf builtin festlegen,
6. sonst `dxgi.dll`.

Eine vorhandene Datei wird nie überschrieben: Sie kommt nach `ScalerAssistant/backup` (bei DLSS 3.7 `HelixSR/backup`) und beim Entfernen zurück.

### 3. Steam-Startoptionen: nur das Nötige, deine bleiben, wie sie sind

`dxgi.dll` und `d3d12.dll` werden unter Proton ohne Weiteres geladen. Jeder andere Name braucht `WINEDLLOVERRIDES="<name>=n,b"` in den Startoptionen, und der Scaler-Assistent trägt es ein:

- **Nur dieser eine Eintrag wird eingefügt.** Hast du schon `WINEDLLOVERRIDES`, wird `;winmm=n,b` darin angehängt; sonst wird `WINEDLLOVERRIDES="winmm=n,b"` vorangestellt (mit `%command%`, falls es fehlte). Alles andere bleibt. Beispiel: `-dx12 %command%` wird zu `WINEDLLOVERRIDES="winmm=n,b" -dx12 %command%`.
- **Nur dieser eine Eintrag wird wieder entfernt**, wenn OptiScaler entfernt oder umbenannt wird. Hast du die Optionen dazwischen nicht geändert, sind sie danach exakt wie vorher; sonst wird nur der eingefügte Text entfernt und deine Änderungen bleiben.
- Einen Eintrag, den du für den Namen schon hattest, lässt er in Ruhe und entfernt ihn auch später nicht. Setzen deine Optionen den Namen auf Wines builtin-Version, nimmt er einen anderen Namen, statt deine Einstellung zu ändern.
- Fehlt der Eintrag später, zeigt das Spiel „Startoption fehlt“, und „Reparieren“ fügt ihn wieder ein.
- Läuft Steam, werden die Optionen über Steam selbst geändert, wenn dessen Debug-Port erreichbar ist (wie ihn Decky Loader nutzt). Sonst bietet der Scaler-Assistent an, Steam zu beenden, die Änderung zu schreiben und Steam neu zu starten — bevor irgendeine Spieldatei angefasst wird.

### 4. Downloads (FSR 4.1 und FSR 3)

Klicke oben auf die **OptiScaler**-Plakette (oder die GPU-Plakette):

- **OptiScaler 0.9.4** (mit AMDs FidelityFX-DLLs: FSR 3 und AMDs FSR 4.1, dazu fakenvapi) und **FSR 4.1 Exact / Lossy / Lite / Lite Lossy** im Build für deine GPU: RX-7000-Karten, RX-6000-Karten, im Prozessor eingebaute RDNA-3-Grafik (auch GeForce, Intel Arc und andere GPUs) oder Steam Deck und im Prozessor eingebaute RDNA-2-Grafik. Jeder Build läuft auf allen; der für deine GPU ist der schnellste. Stürzt ein Spiel mit Exact ab, wähle einen Build für eingebaute Grafik.
- Nichts wird ohne deine Zustimmung geladen. Jeder Download ist ein festes Release, vor dem Entpacken gegen Größe und SHA-256 geprüft; nur die Dateien, die Spiele brauchen, bleiben in `~/.local/share/scaler-assistant/components/`.
- **FSR-4.1-Build**: automatisch nach GPU (RX 9000 / RDNA 4 → AMDs eigenes FSR 4.1, integrierte Grafik und Steam Deck → Build für integrierte Grafik, andere GPUs → Build für Grafikkarten) oder von Hand. Auf RDNA 4 werden die veränderten DLLs nie genutzt. Auf anderen GPUs wird OptiScaler auf das INT8-Modell von FSR 4 gestellt.
- „Downloads entfernen“ löscht sie; Spiele behalten ihre Kopien.

### 5. Was sich in OptiScaler.ini ändert

Nur die Zeilen, die die Wahl braucht, in ihren eigenen Abschnitten; alle anderen Zeilen und Kommentare bleiben:

| Schlüssel | FSR 4.1 | FSR 3 |
|---|---|---|
| `Dx12Upscaler` | `fsr31` | `fsr31` |
| `Dx11Upscaler`, `VulkanUpscaler` | `fsr31_12` (über Direct3D 12) | `fsr31` (nativ) |
| `UpscalerIndex` | `0` (FSR 4) | `1` (FSR 3.1.5) |
| `Fsr4Update` | `true` | `false` |
| `Fsr4ForceEnableInt8` | `true` vor RDNA 4 | `auto` |
| `FfxDx12Path`, `FfxDx12SRPath`, `FfxDx12FGPath`, `FfxVkPath` | die DLLs im `ScalerAssistant`-Ordner des Spiels | ebenso |

Eine schon vorhandene `OptiScaler.ini` wird vorher gesichert und beim Entfernen zurückgelegt.

### 6. Wechseln, aktualisieren, reparieren, entfernen

- **Wechseln** im Upscaler-Menü: Die aktuelle Wahl wird zuerst entfernt, dann die neue installiert. Zwischen FSR 4.1 Exact, Lossy und FSR 3 ändern sich nur die FSR-DLL und `OptiScaler.ini`.
- **Aktualisieren**: Ein Spiel zeigt „↑ HelixSR … verfügbar“, wenn dein HelixSR-Ordner einen neueren Build hat, oder „↑ Neuerer Download verfügbar“, wenn ein neuerer OptiScaler-/FSR-4.1-Download (oder ein anderer FSR-4.1-Build) gilt. „↑ Alle aktualisieren“ erledigt alle Spiele.
- **Reparieren**: Ein Spiel-Update oder „Spieldateien auf Fehler überprüfen“ kann die eigenen Dateien des Spiels zurückbringen. Das Spiel zeigt dann, was passiert ist, und „Reparieren“ bringt den Upscaler zurück; die neuen Dateien des Spiels bleiben als Sicherung.
- **Entfernen** stellt jede ersetzte oder verschobene Datei zurück und nimmt den Startoptionen-Eintrag wieder heraus.

### 7. HelixSR-Einstellungen ohne Dateibearbeitung

Für DLSS 3.7 bearbeitet „⚙ Einstellungen“ die `helixsr.ini` des Spiels als Formular (Schärfung, int8-Netz, letzter Schritt bei Ultra-Leistung, Wave-Größe). „Standard“ lässt die Zeile weg; andere Zeilen und Kommentare bleiben.

### 8. Live-Status und Einblendung

- Laufende Steam-Spiele werden alle 3 Sekunden geprüft: `/proc/<pid>/maps` zeigt, ob das Spiel HelixSR oder die FSR-DLL (und OptiScaler oder den DLSS-Lader) **wirklich geladen** hat. Geladen wird erst, wenn das Spiel den Upscaler nutzt; „noch nicht geladen“ sagt dir also, was du im Spiel wählen musst.
- Bei HelixSR zeigt die `helixsr.log` des aktuellen Laufs Wave-Größe und Fehler; ab RDNA 3 mit dem OptiScaler-Weg wird bei wave32 „WaveSize = 64 setzen“ angeboten.
- Das Detailfeld eines Spiels (die ⌄-Taste auf seiner Karte) bietet „…log anzeigen“ für `helixsr.log` oder `OptiScaler.log`, den Spielordner, OptiScalers Dateinamen und für DLSS 3.7 „⚙ Einstellungen“.
- Beim Spielstart erscheint unten rechts etwa 10 Sekunden lang eine kleine Karte mit dem Ergebnis (oder nach 90 Sekunden ein Hinweis). Sie ist ein eigenes X11-Fenster, das nie den Fokus nimmt; abschaltbar über den Schalter in der Werkzeugleiste.

### 9. Starten, suchen, filtern, Sprachen

- „▶ Starten“ startet das Spiel über Steam. Suche nach Name (jede Sprache) oder App-ID; Filter: hochskalierbare Spiele, Upscaler installiert, noch kein Upscaler, Update oder Reparatur nötig, läuft, alle Spiele.
- 12 Oberflächensprachen: 台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी.

### 10. Auf Sicherheit gebaut

- Solange das Spiel läuft, ändert sich nichts; Downloads und HelixSR-Ordner werden geprüft, bevor eine Datei angefasst wird.
- Jede ersetzte Datei wird behalten, jede Kopie Byte für Byte geprüft, und Startoptionen ändern sich nur um den oben beschriebenen einen Eintrag.
- Der DLSS-Weg, FSR 4.1 Lossy und Spiele mit Anti-Cheat fragen vorher. Nutze nie einen veränderten Upscaler in Online-Spielen: Anti-Cheat kann das als Manipulation werten.

### 11. Aussehen

- Im Stil von MAKO Assistant („Liquid Glass“): eine Karte pro Spiel mit Steam-Cover, Status-Chip, dem, was das Spiel bietet, und während es läuft, dem, was wirklich geladen ist. Die ⌄-Taste öffnet die Details (Grafik-API, Upscaler, `.exe`-Ordner, OptiScalers Name, Startoptionen) und seltenere Aktionen.
- Tasten sind erhabener, klarer Kristall: leichte Tönung mit feinem Rand, ein gebogener Glanz auf der oberen Hälfte, ein Lichtsaum am unteren Rand und ein weicher Schatten darunter – alles flache, durchscheinende Ebenen, keine Verläufe. Schalterknöpfe heben sich ebenso ab; das gewählte Design-Segment ist ein erhabener Kristall in einer vertieften Spur. Türkis installiert, Blau wechselt, Bernstein aktualisiert, Rot entfernt.
- Dunkles, helles oder automatisches Design (folgt dem Desktop). Das Aktivitätsprotokoll ist die Schublade am unteren Fensterrand.

## HelixSR 2.0 und die GPU

- **HelixSR in einem Schritt herunterladen und erstellen**: „HelixSR herunterladen und erstellen“ (im HelixSR-Fenster und im Steam-Deck-Plugin) lädt das neueste HelixSR (2.0 oder neuer) aus seinen GitHub-Releases, per SHA-256 geprüft, nach `~/.local/share/scaler-assistant/helixsr` und erstellt es auf diesem PC mit HelixSRs eigenem Build-Programm (`setup/helixsr_setup.py`, unverändert ausgeführt) – so wie HelixSRs eigene App, also ohne Terminal und ohne Spiele-Schritt. Was der Build braucht, wird mitgebracht: ein Python mit numpy (ein portables Python 3.14, wenn das System-Python NVIDIAs zstd-Paket nicht entpacken kann, damit die Frame-Generation kein zusätzliches `zstd` braucht) und Microsofts DirectX Shader Compiler, ausgeführt über Steams Proton oder Wine. NVIDIAs Dateien werden erst nach deiner Zustimmung in der App geladen; das Ergebnis bleibt auf deinem PC. In Flatpak läuft der Build auf dem Host. Ein erneuter Lauf erstellt nur, was fehlt; ein neueres Release ersetzt das zuvor geladene.
- **HelixSR 2.0 und neuer** legen die gebaute DLL in `HelixSR-fsrfg` ab und bieten zwei Wege: **HelixSR Scaler** (HelixSRs eigener OptiScaler-Build neben der `.exe`: im Spiel DLSS wählen; auch DX11- und Vulkan-Spiele) und den **FSR-Weg** (FSR-Drop-in). Scaler-Assistent installiert beide über das Installationsprogramm in deinem HelixSR-Ordner (`setup/helixsr_bridge.py`, das auch HelixSRs eigene App nutzt), sodass HelixSRs Setup, seine App und Scaler-Assistent die Installationen der anderen erkennen, aktualisieren und entfernen. Den Dateinamen wählt weiterhin Scaler-Assistent, und er fügt bei Bedarf die Startoption hinzu. Spiele mit einem früheren Weg wechseln beim Aktualisieren zu HelixSR Scaler. HelixSR-1.8-/1.9-Ordner behalten ihre drei Wege.
- **HelixSR-Frame-Generation** (HelixSR 2.0): In DirectX-12-Spielen mit DLSS Frame Generation (Streamlines `sl.dlss_g.dll`) bekommt ein Spiel mit HelixSR Scaler auf seiner Karte (und im Steam-Deck-Plugin) einen Schalter „HelixSR-Frame-Generation“. Er nutzt HelixSRs eigenen Installer (`scaler-fg`), der nur die `[FrameGen]`-Auswahl in OptiScaler.ini ändert; danach im Spiel DLSS Frame Generation einschalten. Nötig ist die Frame-Generation, die `./helixsr-setup.sh` erstellt (es lädt NVIDIAs DLSS-Frame-Generation-Dateien herunter); bis dahin ist der Schalter mit Begründung ausgegraut. Neue Installationen lassen sie aus; ein Update oder ein neuer OptiScaler-Dateiname behält den Zustand. Andere DX12-Spiele können im Menü von HelixSR Scaler (Einfg) weiter AMD-FSR- oder XeSS-Frame-Generation wählen; DX11-/Vulkan-Spiele und der FSR-Weg bekommen nur Upscaling.
- **HelixSR 3.0**: Die erstellte DLL ist `HelixSR/helixsr.dll` (HelixSR Scalers DLSS-Upscaler „HLX DLSS“), und der FSR-Weg setzt **HLX FSR 4** ein, HelixSRs eigene FSR-4-Pipeline, die HelixSRs Setup aus AMDs FSR-4-Treiberdatei erstellt (es lädt etwa 420 MB aus AMDs Treiberpaket von AMD; „HelixSR herunterladen und erstellen“ fragt vorher und bringt auch den zweiten Shader-Compiler DXC 1.9.2609 mit). Der Scaler-Assistent installiert, aktualisiert, wechselt und entfernt beide Wege wie bei 2.0 über den Installer der Release; mit 2.0 eingerichtete Spiele ziehen beim Update von `HelixSR-fsrfg` nach `HelixSR` um. HelixSR 3.0 hat keine Frame-Generation, daher erscheint der Schalter oben damit nicht; AMD-FSR- und XeSS-Frame-Generation bleiben im Menü von HelixSR Scaler. Ab HelixSR 3.2 liegt HLX FSR 4 fertig gebaut in der ZIP (aus AMDs FSR SDK 2.4.0, FSR 4.1.2): Das Setup lädt AMDs Treiberpaket nicht mehr herunter, und AMDs eigenes FSR daneben in HelixSR Scaler ist FSR 4.1.2. HelixSR 3.2.1 bringt ein optionales **Preset K** für HLX DLSS, das nur HelixSRs eigenes Setup erstellt (`--preset-k`; „HelixSR herunterladen und erstellen“ erstellt es nicht): Ist es erstellt, kommt es mit HelixSR Scaler ins Spiel (`HelixSR/k`) und mit ihm wieder heraus, sein Log eingeschlossen. HelixSR 3.3 (HelixSR Scaler 2.3.0) behält diesen Aufbau: HelixSR Scaler listet HLX FSR 4 jetzt auch in Vulkan-Spielen, und „HelixSR herunterladen und erstellen“ baut auch die Vulkan-Kernel von HLX DLSS (`--vulkan` des Setups), sodass HLX DLSS in Vulkan-Spielen nativ läuft statt über HelixSR Scalers DirectX-12-Brücke. Das verdoppelt etwa die Build-Zeit und braucht viel Arbeitsspeicher; ein schon ohne sie erstelltes 3.3 wird neu erstellt (scheitern sie, bleibt das zuvor erstellte Netzwerk in Gebrauch und Vulkan-Spiele nutzen die Brücke). 3.3 liefert HLX FSR 4 fertig gebaut ohne sein Build-Programm, daher lädt „HelixSR herunterladen und erstellen“ dafür kein DXC 1.9.2609 mehr.
- **Frühere HelixSR-Versionen**: 1.8.x bietet alle drei Wege (FSR-Weg, OptiScaler-Weg, DLSS-Weg). HelixSR 1.9.0 – 1.9.3 enthalten nur die Dateien des FSR-Wegs, daher sind OptiScaler- und DLSS-Weg dort ausgegraut („braucht HelixSR 1.8 oder 2.0“); Spiele ohne FSR 3.1 brauchen HelixSR 2.0 (HelixSR Scaler). Versionen vor 1.8.0 werden nicht unterstützt.
- **DLSS-Weg nur mit einer GeForce**: Mit einer AMD- oder Intel-GPU bieten Spiele DLSS nicht zur Auswahl an, daher ist der DLSS-Weg (HelixSR 1.x) mit Begründung ausgegraut.
- **FSR 4.1.2 Lite Lossy empfohlen** bei integrierter Grafik (Steam Deck, ROG Ally Z1 / Z2, Ryzen AI MAX) und Intel-GPUs: nur unter den FSR-4.1-Optionen als „★ Empfohlen“ markiert.

## Zusammenarbeit mit HelixSRs eigenem Setup

Für DLSS 3.7 schreibt der Scaler-Assistent denselben Installationsdatensatz (`helixsr-install.json`), dieselben Sicherungen und Dateinamen wie HelixSRs Setup, daher erkennen `helixsr-setup.sh` / `helixsr-uninstall.sh` und der Scaler-Assistent die Spiele des jeweils anderen. HelixSRs Setup hält die FSR-DLL im `ScalerAssistant`-Ordner eines Spiels für die FSR-3.1-DLL des Spiels und kann sie durch HelixSR ersetzen; der Scaler-Assistent meldet das Spiel dann als reparaturbedürftig, und „Reparieren“ nimmt HelixSR wieder heraus. Für DLSS 3.7 in einem solchen Spiel wähle es im Scaler-Assistenten.

## Steam-Deck-Plugin (Decky Loader)

Dasselbe Programm für den Spielmodus, als Plugin für [Decky Loader](https://decky.xyz) im Schnellzugriffsmenü.

- **Spiele**: die Spiele, die hochskaliert werden können, laufende zuerst, jeweils mit Status-Chip und, während sie laufen, dem, was wirklich geladen ist. Ein Spiel auswählen, um DLSS 3.7 (HelixSR, jeder Weg), FSR 4.1 Exact / Lossy oder FSR 3 zu wählen, es zu aktualisieren, zu reparieren oder zu entfernen, OptiScalers Dateinamen zu ändern oder sein Log zu lesen. Vorher kommen dieselben Fragen wie in der Desktop-App: Downloads, die Lossy-Warnung, der DLSS-Weg und Anti-Cheat.
- **Einrichtung**: der HelixSR-Ordner (Dateiauswahl), die Downloads und der FSR-4.1-Build (das Steam Deck bekommt den Build für integrierte Grafik), ein Hinweis beim Spielstart (ob der Upscaler geladen wurde) und die Sprache (standardmäßig wie Steam).
- Es teilt `state.json`, die Downloads und die Startoptions-Einträge mit der Desktop-App; in einem eingerichtete Spiele erscheinen auch im anderen. Startoptionen werden live über Steam geschrieben.
- Nicht im Plugin: das Formular für HelixSRs Einstellungen (Desktop-App verwenden) und HelixSRs eigenes `helixsr-setup.sh`, das du einmal im Desktopmodus ausführst.
- Im Plugin lädt und erstellt **HelixSR herunterladen und erstellen** HelixSR 2.0 oder neuer auch im Spielmodus (dauert einige Minuten).

Installation: Decky Loader auf dem Steam Deck einrichten, `Scaler_Assistant-Decky-<Version>.zip` von der [Releases](https://github.com/mosesmoon/scaler-assistant/releases)-Seite laden, dann in Deckys Einstellungen → Entwickler (zuerst unter Allgemein den Entwicklermodus einschalten) → „Install Plugin from ZIP File“.

## Den Scaler-Assistenten installieren

**AppImage (empfohlen)**: Python, Qt und 7-Zip sind enthalten.

1. `Scaler_Assistant-<version>-x86_64.AppImage` von der [Releases](https://github.com/mosesmoon/scaler-assistant/releases)-Seite laden.
2. Ausführbar machen: Rechtsklick → Eigenschaften → Berechtigungen → „Als Programm ausführen“ (je nach Dateimanager anders benannt).
3. Doppelklicken.

```bash
chmod +x Scaler_Assistant-*-x86_64.AppImage
./Scaler_Assistant-*-x86_64.AppImage
```

Startet es nicht, fehlt eventuell FUSE; dann mit `--appimage-extract-and-run` starten.

**Einzelinstaller (.bin)**: `Scaler_Assistant-<Version>-x86_64.bin` installiert dieselbe gebündelte App nur für deinen Benutzer (ohne root, ohne FUSE) nach `~/.local/opt/scaler-assistant`, mit dem Befehl `scaler-assistant` und einem Menüeintrag. **Flatpak**: `Scaler_Assistant-<Version>-x86_64.flatpak` ist ein Ein-Datei-Bundle auf der Freedesktop-25.08-Runtime (bei der Installation von Flathub geladen). Es darf deinen Home-Ordner und andere Laufwerke (SD-Karten unter `/run/media`) lesen und sieht Steams und die Spielprozesse über `flatpak-spawn --host`.

```bash
sh Scaler_Assistant-*-x86_64.bin                # install / installieren
sh Scaler_Assistant-*-x86_64.bin --uninstall    # remove / entfernen
flatpak install --user Scaler_Assistant-*-x86_64.flatpak
flatpak run io.github.mosesmoon.ScalerAssistant
```

**Aus dem Quellcode**: Python 3.11+ und PyQt6 (Arch: `sudo pacman -S python-pyqt6`), dazu 7-Zip oder bsdtar zum Entpacken von OptiScaler (`sudo pacman -S 7zip`).

```bash
./scaler-assistant     # direkt starten
./install.sh           # nach ~/.local/share/scaler-assistant installieren und Menüeintrag anlegen
```

## Bekannte Einschränkungen

- **Nur Steam-Spiele.** Die FSR-4.1-/FSR-3-Wege wurden Datei für Datei mit OptiScaler 0.9.4 geprüft; jedes Spiel verhält sich anders — bei Problemen OptiScalers Kompatibilitätsliste ansehen oder einen anderen Dateinamen für OptiScaler wählen.
- FSR 4.1 in Direct3D-11- und Vulkan-Spielen läuft über OptiScalers Direct3D-12-Pfad und ist weniger getestet.
- HelixSR ändert sich schnell. Der Scaler-Assistent braucht HelixSR 1.8.0 oder neuer und folgt dem Aufbau von 1.8.x / 1.9.x / 2.0.x / 3.0.x / 3.1.x / 3.2.x / 3.3.x.
- Im Spielmodus des Steam Deck (gamescope) erscheint die Einblendung nicht. Das Decky-Plugin zeigt dort stattdessen eine Steam-Benachrichtigung.
- Auf Thai, Vietnamesisch, Malaiisch und Hindi sind Kontextmenüs englisch (Qt hat keine offiziellen Übersetzungen). Steam hat keine malaiischen oder Hindi-Spielnamen.

## Wo Daten liegen

| Ort | Inhalt |
|---|---|
| `~/.config/scaler-assistant/state.json` | Zustand des Scaler-Assistenten: HelixSR-Ordner, Spieleliste, Sprache, FSR-4.1-Build, gewählte OptiScaler-Namen, die von ihm eingefügten Startoptionen-Einträge (einmalig vom HelixSR-Assistenten übernommen) |
| `~/.local/share/scaler-assistant/components/` | Die heruntergeladenen OptiScaler- und FSR-4.1-Dateien |
| `~/homebrew/plugins/scaler-assistant/` | Das Decky-Plugin auf dem Steam Deck (nutzt denselben Zustand und dieselben Downloads wie oben) |
| `<Spiel>/…/ScalerAssistant/` | FSR 4.1 / FSR 3: FidelityFX-DLLs, `scaler-install.json`, `backup/` |
| `<Spiel>/…/HelixSR/helixsr-install.json`, neben der FSR-DLL des Spiels | DLSS 3.7: HelixSRs Installationsdatensatz (mit HelixSRs Setup geteilt) |
| `<Spiel>/…/helixsr.ini`, `helixsr.log`, `OptiScaler.ini`, `OptiScaler.log` | Einstellungen und Protokolle |

## Lizenzen

Der Scaler-Assistent ist ein unabhängiges, inoffizielles Werkzeug, nicht verbunden mit oder unterstützt von HelixSRs Autor, NVIDIA, AMD, dem OptiScaler-Projekt oder dem Projekt fsr4-shader-performance-overrides, und enthält keine ihrer Dateien. Auf deinen Wunsch lädt er OptiScaler (GPL-3.0; fakenvapi MIT; AMDs FidelityFX-DLLs unter AMDs Lizenz) und die FSR-4.1-DLLs (GPL-2.0-or-later, veränderte AMD-DLLs mit AMDs Hinweis) von deren GitHub-Releases. Das AppImage enthält 7-Zips `7zzs` (GNU LGPL mit unRAR-Einschränkung, BSD; Lizenz liegt bei). HelixSR ist unter der HelixSR Freeware License kostenlos; nach seinem Setup enthalten HelixSRs DLLs NVIDIAs Netz, daher kopiert der Scaler-Assistent sie nur zwischen Ordnern auf deinem eigenen PC. Teile oder lade sie niemals hoch. Das Decky-Plugin enthält dasselbe `7zzs`.
