# HelixSR-Assistent — Funktionsübersicht

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · **Deutsch** · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

Der **HelixSR-Assistent** ist ein Linux-Desktop-Werkzeug, das **[HelixSR](https://github.com/lonewolf0622/HelixSR)** mit einem Klick in deine Steam-Spiele installiert, umstellt, aktualisiert und wieder entfernt – und beim Spielen zeigt, ob HelixSR wirklich läuft.

HelixSR lässt NVIDIAs DLSS-Model-E-Upscaling-Netz über Proton als gewöhnliche Direct3D-12-Compute-Shader auf AMD-GPUs (RDNA 1 und neuer) laufen.

## Für wen ist das Werkzeug?

HelixSR hat weder Startoptionen noch eine zentrale Einstellungsdatei. Es legt DLL-Dateien in den Ordner jedes Spiels, auf einem von drei Wegen pro Spiel. Von Hand heißt das:

1. Herausfinden, welche Upscaler jedes Spiel mitbringt (FSR 3.1, DLSS, XeSS, FSR 2) und wo seine Haupt-`.exe` liegt.
2. Den passenden Weg wählen, die eigenen Dateien des Spiels umbenennen und sichern und die Dateien von HelixSR an die richtigen Stellen kopieren.
3. Beim OptiScaler-Weg die richtigen Pfade in `OptiScaler.ini` eintragen.
4. Alles nach jedem HelixSR-Update wiederholen – und erneut, wenn ein Spiel-Update HelixSR überschreibt.
5. `helixsr.log` öffnen, um herauszufinden, ob HelixSR wirklich läuft.

Der HelixSR-Assistent erledigt all das in einem Fenster. HelixSRs eigenes Setup fragt im Terminal Spiel für Spiel; der HelixSR-Assistent zeigt sie als Liste zum Anklicken.

## Bevor du anfängst

> ⚠ **Der HelixSR-Assistent enthält HelixSR nicht und lädt es auch nicht für dich herunter.** Er kopiert nur Dateien aus dem HelixSR-Ordner, den du selbst eingerichtet hast.

1. **HelixSR herunterladen** (1.8.0 oder neuer) von seinen [GitHub-Releases](https://github.com/lonewolf0622/HelixSR/releases) und in einen Ordner entpacken, den du behältst, zum Beispiel dein Home-Verzeichnis.
2. **Einmal `./helixsr-setup.sh` in diesem Ordner ausführen.** Es fragt, ob NVIDIAs DLSS-DLL heruntergeladen werden darf, und erstellt daraus das Netz von HelixSR (etwa eine Minute). Sobald es nach Spielen fragt, kannst du mit `n` antworten oder das Fenster schließen: Um die Spiele kümmert sich der HelixSR-Assistent. Findet er den Ordner, der aber noch nicht eingerichtet ist, bietet er die Schaltfläche „Setup im Terminal ausführen“ an.
3. **Eine AMD-GPU ab RDNA 1** (Radeon RX 5000 und neuer, Steam Deck, Ryzen-APUs mit RDNA-Grafik). Radeon Vega wird in HelixSR 1.9.0 experimentell unterstützt.
4. **Direct3D-12-Spiele unter Proton**, die FSR 3.1, DLSS, XeSS oder FSR 2 mitbringen.

Beim ersten Start sucht der HelixSR-Assistent in deinem Home-, Download-, Desktop- und Games-Ordner nach einem eingerichteten HelixSR-Ordner. Mit „HelixSR-Ordner wählen…“ oder einem Klick auf die HelixSR-Anzeige oben wählst du jederzeit einen anderen.

## Die drei Wege, wie HelixSR in ein Spiel kommt

Das sind die drei Wege von HelixSR selbst (die Buchstaben sind die Antworten im HelixSR-Setup). Der HelixSR-Assistent bietet nur die Wege an, die für das jeweilige Spiel funktionieren, den Standardweg zuerst.

| Weg | Das Spiel braucht | Was sich im Spielordner ändert | Im Spiel wählen |
|---|---|---|---|
| **FSR-Weg** (f, Standard bei FSR-3.1-Spielen) | FSR 3.1 | Die `amd_fidelityfx_upscaler_dx12.dll` (oder `amd_fidelityfx_dx12.dll`) des Spiels wird durch HelixSR ersetzt; die Datei des Spiels bleibt als `*.original.dll` erhalten | **AMD FSR** |
| **OptiScaler-Weg** (o) | DLSS, XeSS oder FSR 2 | OptiScaler (die offizielle Version aus deinem HelixSR-Ordner) neben der `.exe` des Spiels; sein FSR-3.1-Backend zeigt auf einen `HelixSR`-Ordner daneben. Alles, was er ersetzt, landet in `HelixSR/backup` | **DLSS** (FSR oder XeSS gehen auch) |
| **DLSS-Weg** (d, experimentell) | DLSS | HelixSRs DLSS-Loader als `dxgi.dll` und HelixSR als `nvngx.dll` neben der `.exe` des Spiels | **DLSS** |

## Funktionen

### 1. Liest deine Steam-Spiele und ihre Upscaler ein

- Beim ersten Start werden alle Steam-Bibliotheken eingelesen (auch auf anderen Laufwerken). Nach dem Installieren neuer Spiele auf „⟳ Steam-Spiele neu einlesen“ klicken.
- Der Ordner jedes Spiels wird nach FSR-3.1-, DLSS-, XeSS- und FSR-2-DLLs durchsucht; der Ordner der Haupt-`.exe` wird aus Steams Startinformationen ermittelt (Launcher und Unreal-`*-Shipping.exe` werden berücksichtigt).
- Spiele mit **Anti-Cheat** (Easy Anti-Cheat, BattlEye) werden markiert.
- Spielnamen folgen der Oberflächensprache (Steams lokalisierte Namen) und werden nach den Regeln dieser Sprache sortiert. Spiele, die HelixSR nutzen können, stehen oben; der Filter „Spiele, die HelixSR nutzen können“ ist standardmäßig aktiv.

### 2. Installation mit einem Klick

- „HelixSR installieren“ installiert auf dem Standardweg, der Pfeil daneben bietet die anderen Wege an. Bei jedem Weg steht dabei, was im Spiel zu wählen ist.
- Bevor etwas geändert wird, prüft das Werkzeug, ob der HelixSR-Ordner eingerichtet ist (das Netz erstellt wurde) und das Spiel nicht läuft.
- Der DLSS-Weg erklärt zuerst seine Risiken und fragt nach. Spiele mit Anti-Cheat fragen ebenfalls nach.
- Danach steht im Protokoll genau, welche Dateien ersetzt wurden, wo die Dateien des Spiels gesichert sind und was im Spiel zu wählen ist.

### 3. Weg wechseln, aktualisieren und reparieren

- **Wechseln**: „Mehr“ → „Zum … wechseln“ entfernt zuerst den bisherigen Weg (alles wird zurückgelegt) und installiert dann den neuen. Deine HelixSR-Einstellungen ziehen mit um.
- **Aktualisieren**: Hat dein HelixSR-Ordner einen neueren Build als ein Spiel (neue HelixSR-Version oder neu erstelltes Netz), zeigt das Spiel „↑ HelixSR … verfügbar“ und eine Schaltfläche „↑ Aktualisieren“; „↑ Alle aktualisieren“ erledigt alle Spiele auf einmal.
- **Reparieren**: Ein Spiel-Update oder „Dateien auf Fehler überprüfen“ in Steam kann die eigenen Dateien des Spiels über HelixSR legen. Das Spiel zeigt dann, was passiert ist, und eine Schaltfläche „Reparieren“: Sie legt HelixSR zurück und behält die neuen Dateien des Spiels als Sicherung.
- Taucht in deinem Download-Ordner (oder an einem anderen üblichen Ort) ein neuerer, eingerichteter HelixSR-Ordner auf, bietet das Werkzeug einmal an, zu ihm zu wechseln.

### 4. Entfernen

- „Entfernen“ nimmt HelixSR heraus und legt jede Datei, die es ersetzt oder verschoben hat, genau so zurück, wie sie war.
- Die HelixSR-Einstellungen des Spiels (`helixsr.ini`) bleiben erhalten, außer du hakst „Auch die HelixSR-Einstellungen dieses Spiels entfernen“ an.
- Dateien, die du selbst in den `my-fsr`-Ordner des Spiels gelegt hast, werden nie gelöscht.

### 5. HelixSR-Einstellungen ohne Dateibearbeitung

„⚙ Einstellungen“ bearbeitet die `helixsr.ini` des Spiels über ein Formular. Angeboten werden nur die Einstellungen, die HelixSRs README beschreibt:

| Gruppe | Einstellung | Werte |
|---|---|---|
| Schärfung | Schärfungsfilter | Standard, Aus, NVIDIA, RCAS |
| | Schärfe | 0.00 – 1.00 |
| | Dem Schärferegler des Spiels folgen | Standard, Ja, Nein |
| Upscaling (HelixSR 1.9.0+) | int8-Netz | Standard (automatisch), Automatisch, Ein, Aus |
| | Letzter Schritt bei Ultra-Leistung | Standard (Lanczos), Lanczos, EASU (FSR 1) |
| Kompatibilität | Wave-Größe | Standard, 64, 32 |

„Standard“ lässt die Zeile weg, dann nutzt HelixSR seinen eigenen Standardwert. Kommentare und alle anderen Zeilen der Datei bleiben unverändert. Die Datei liegt neben HelixSRs DLL für den Weg des Spiels (im `HelixSR`-Ordner des Spiels, neben der FSR-DLL des Spiels oder neben der `.exe`).

### 6. HelixSR-Status live (was wirklich läuft)

Laufende Steam-Spiele werden alle 3 Sekunden geprüft:

- Proton lädt Windows-DLLs aus ihren Dateien. Daher sieht das Werkzeug in `/proc/<pid>/maps`, ob das Spiel **HelixSR wirklich geladen hat** (und OptiScaler oder den DLSS-Loader).
- HelixSR wird erst geladen, wenn das Spiel den Upscaler benutzt. „HelixSR noch nicht geladen“ sagt dir deshalb, was du in den Grafikeinstellungen des Spiels wählen musst.
- Die `helixsr.log` des aktuellen Laufs wird gelesen: Die Wave-Größe der Netz-Kernel und eventuelle Fehlerzeilen werden angezeigt. „Mehr“ → „helixsr.log anzeigen“ zeigt das ganze Protokoll mit einer Kopierschaltfläche.
- Auf GPUs **ab RDNA 3** empfiehlt HelixSRs README in Spielen mit OptiScaler-Weg `WaveSize = 64`, wenn das Protokoll wave32 meldet. Das Werkzeug erkennt das und bietet „WaveSize = 64 setzen“ mit einem Klick an.
- Die GPU-Anzeige oben zeigt die Generation deiner GPU (zum Beispiel „AMD RDNA 3 (gfx1100)“).

### 7. Einblendung beim Spielstart

Ist der HelixSR-Assistent beim Start eines Spiels mit HelixSR geöffnet, erscheint unten rechts für etwa 10 Sekunden eine kleine Karte, sobald HelixSR geladen ist – mit Version, Weg und Wave-Größe (einmal pro Start; Spiele, die schon vor dem Öffnen liefen, werden übersprungen). Ist HelixSR nach 90 Sekunden noch nicht geladen, sagt die Karte, was im Spiel zu wählen ist. Die Einblendung ist ein eigenes X11-Fenster (XWayland), nimmt nie den Fokus und lässt Mausklicks durch. Abschaltbar über das Kästchen in der Werkzeugleiste. Im Spielmodus des Steam Deck (gamescope) erscheint sie nicht.

### 8. Spiele starten, suchen und filtern

- Jede Zeile hat eine Schaltfläche „▶ Starten“ (über `steam://rungameid/<AppID>`); solange das Spiel läuft, steht dort „Läuft“.
- Suche nach Spielname (in jeder Sprache) oder App-ID. Filter: Spiele, die HelixSR nutzen können, installiert, nicht installiert, Update oder Reparatur nötig, läuft, alle Spiele.

### 9. Zwölf Oberflächensprachen

台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी. Beim ersten Start wird die Systemsprache verwendet; oben rechts umschalten (sofort wirksam und gespeichert).

### 10. Auf Sicherheit ausgelegt

- Es wird nichts geändert, solange der HelixSR-Ordner nicht eingerichtet ist oder das Spiel läuft.
- Jede Datei, die HelixSR ersetzt, wird aufbewahrt (`*.original.dll` oder `HelixSR/backup`), und jede kopierte Datei wird Byte für Byte geprüft.
- Eine vorhandene `OptiScaler.ini` wird gesichert und beim Entfernen zurückgelegt; eine FSR-DLL, die du im `HelixSR`-Ordner des Spiels von Hand ersetzt hast, bleibt bei Updates erhalten.
- Der DLSS-Weg und Spiele mit Anti-Cheat erfordern eine ausdrückliche Bestätigung.

## Zusammenarbeit mit HelixSRs eigenem Setup

Der HelixSR-Assistent schreibt denselben Installationsvermerk (`helixsr-install.json`), dieselben Sicherungen und Dateinamen wie HelixSRs Setup. Daher:

- Spiele, die du mit `helixsr-setup.sh` eingerichtet hast, erscheinen im HelixSR-Assistenten als installiert (mit ihrem Weg) und lassen sich dort umstellen, aktualisieren oder entfernen.
- Mit dem HelixSR-Assistenten eingerichtete Spiele erkennen auch HelixSRs Setup und `helixsr-uninstall.sh`, die sie aktualisieren oder entfernen können.

## HelixSR-Assistent installieren

**AppImage (empfohlen)**: Python und Qt sind enthalten, sonst muss nichts installiert werden.

1. `HelixSR_Assistant-<Version>-x86_64.AppImage` von der Seite [Releases](https://github.com/mosesmoon/helixsr-assistant/releases) herunterladen.
2. Ausführbar machen: Rechtsklick auf die Datei → Eigenschaften → Berechtigungen und „Datei als Programm ausführen“ einschalten (die Bezeichnung hängt vom Dateimanager ab).
3. Doppelklicken, um den HelixSR-Assistenten zu öffnen.

Oder im Terminal:

```bash
chmod +x HelixSR_Assistant-*-x86_64.AppImage
./HelixSR_Assistant-*-x86_64.AppImage
```

Startet es nicht, fehlt deinem System eventuell FUSE; starte es dann mit `./HelixSR_Assistant-*-x86_64.AppImage --appimage-extract-and-run`.

**Aus dem Quellcode**: benötigt Python 3.11 oder neuer und PyQt6 (Arch: `sudo pacman -S python-pyqt6`).

```bash
./helixsr-assistant    # direkt starten
./install.sh           # nach ~/.local/share/helixsr-assistant installieren und einen Menüeintrag anlegen
```

## Bekannte Einschränkungen

- **Nur Steam-Spiele.** Für Spiele aus anderen Stores HelixSRs eigenes Setup verwenden (den Ordner des Spiels hineinziehen).
- HelixSR selbst funktioniert nur in Direct3D-12-Spielen. Ein Spiel mit DLSS- oder FSR-DLL kann trotzdem Vulkan oder Direct3D 11 nutzen; dann bewirkt HelixSR dort nichts.
- HelixSR ändert sich sehr schnell. Der HelixSR-Assistent braucht HelixSR 1.8.0 oder neuer und wurde für den Aufbau von 1.8.x und 1.9.x gemacht. Ändert eine künftige HelixSR-Version die Einrichtung der Spiele, verwende HelixSRs eigenes Setup, bis der HelixSR-Assistent aktualisiert ist.
- Die Einblendung erscheint nicht im Spielmodus des Steam Deck (gamescope); Spiele im exklusiven nativen Wayland-Vollbild können sie verdecken.
- Auf Thai, Vietnamesisch, Malaiisch und Hindi sind Kontextmenüs englisch (Qt hat für diese Sprachen keine offiziellen Übersetzungen). Steam hat keine malaiischen oder Hindi-Spielnamen, daher zeigen diese beiden Sprachen immer die Originalnamen.

## Wo Daten gespeichert werden

| Ort | Inhalt |
|---|---|
| `~/.config/helixsr-assistant/state.json` | Eigener Zustand des HelixSR-Assistenten: HelixSR-Ordner, Spielelisten-Cache, Oberflächensprache, Einblendungs-Einstellung |
| `<Spiel>/…/HelixSR/helixsr-install.json`, neben der FSR-DLL des Spiels | HelixSRs Installationsvermerk (gemeinsam mit HelixSRs eigenem Setup) |
| `<Spiel>/…/helixsr.ini` | HelixSRs Einstellungen für dieses Spiel |
| `<Spiel>/…/helixsr.log` | Was HelixSR beim letzten Spielstart gemeldet hat |

## Lizenzen

Der HelixSR-Assistent ist ein unabhängiges, inoffizielles Werkzeug. Er steht in keiner Verbindung zum Autor von HelixSR, zu NVIDIA, AMD oder dem OptiScaler-Projekt, wird von ihnen nicht unterstützt und enthält keine ihrer Dateien. HelixSR ist unter der HelixSR Freeware License kostenlos nutzbar. Nach dem Setup von HelixSR enthalten HelixSRs DLLs NVIDIAs Netz: Der HelixSR-Assistent kopiert sie nur zwischen Ordnern auf deinem eigenen PC. Teile oder lade sie niemals hoch.
