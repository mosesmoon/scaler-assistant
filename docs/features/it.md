# Assistente HelixSR — Guida alle funzioni

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · **Italiano** · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

L'**Assistente HelixSR** è uno strumento desktop per Linux che installa, cambia metodo, aggiorna e rimuove **[HelixSR](https://github.com/lonewolf0622/HelixSR)** nei tuoi giochi Steam con un clic, e mostra mentre giochi se HelixSR sta funzionando davvero.

HelixSR esegue la rete di upscaling DLSS Model E di NVIDIA sulle GPU AMD (RDNA 1 e successive) come normali compute shader Direct3D 12, tramite Proton.

## A chi è rivolto

HelixSR non ha opzioni di avvio né un file di impostazioni centrale. Funziona mettendo delle DLL nella cartella di ogni gioco, con uno di tre metodi per gioco. Farlo a mano significa:

1. Scoprire quali upscaler ha ogni gioco (FSR 3.1, DLSS, XeSS, FSR 2) e dove si trova il suo `.exe` principale.
2. Scegliere il metodo giusto, rinominare i file del gioco per conservarli e copiare i file di HelixSR nei posti giusti.
3. Con il metodo OptiScaler, scrivere i percorsi corretti in `OptiScaler.ini`.
4. Rifare tutto a ogni aggiornamento di HelixSR, e di nuovo quando un aggiornamento del gioco sovrascrive HelixSR.
5. Aprire `helixsr.log` per capire se HelixSR sta funzionando davvero.

L'Assistente HelixSR fa tutto questo da un'unica finestra. L'installazione di HelixSR chiede gioco per gioco in un terminale; l'Assistente li mostra in un elenco da cliccare.

## Prima di iniziare

> ⚠ **L'Assistente HelixSR non include HelixSR e non lo scarica mai al posto tuo.** Copia soltanto file dalla cartella di HelixSR che hai preparato tu.

1. **Scarica HelixSR** (1.8.0 o successivo) dalle sue [release su GitHub](https://github.com/lonewolf0622/HelixSR/releases) ed estrailo in una cartella da conservare, per esempio la tua cartella home.
2. **Esegui una volta `./helixsr-setup.sh` in quella cartella.** Chiede se scaricare la DLL DLSS di NVIDIA e da essa crea la rete di HelixSR (circa un minuto). Quando inizia a chiedere dei giochi, puoi rispondere `n` o chiudere la finestra: dei giochi si occupa l'Assistente HelixSR. Se trova la cartella ma non è ancora pronta, l'Assistente offre il pulsante «Esegui l'installazione in un terminale».
3. **Una GPU AMD RDNA 1 o successiva** (Radeon RX 5000 e successive, Steam Deck, APU Ryzen con grafica RDNA). Il supporto a Radeon Vega è sperimentale in HelixSR 1.9.0.
4. **Giochi Direct3D 12 eseguiti tramite Proton** che includono FSR 3.1, DLSS, XeSS o FSR 2.

Al primo avvio l'Assistente HelixSR cerca una cartella di HelixSR pronta nelle cartelle home, Scaricati, Scrivania e Games. Puoi sempre sceglierne un'altra con «Scegli cartella di HelixSR…» o facendo clic sull'indicatore HelixSR in alto.

## I tre metodi per portare HelixSR in un gioco

Sono i tre metodi di HelixSR stesso (le lettere sono le risposte usate dalla sua installazione). L'Assistente HelixSR propone solo quelli che funzionano per ogni gioco, con quello predefinito per primo.

| Metodo | Il gioco deve avere | Cosa cambia nella cartella del gioco | Da scegliere nel gioco |
|---|---|---|---|
| **Metodo FSR** (f, predefinito per i giochi FSR 3.1) | FSR 3.1 | `amd_fidelityfx_upscaler_dx12.dll` (o `amd_fidelityfx_dx12.dll`) del gioco viene sostituito da HelixSR; il file del gioco è conservato come `*.original.dll` | **AMD FSR** |
| **Metodo OptiScaler** (o) | DLSS, XeSS o FSR 2 | OptiScaler (la versione ufficiale nella tua cartella di HelixSR) accanto al `.exe` del gioco, con il suo backend FSR 3.1 puntato a una cartella `HelixSR` vicina; tutto ciò che sostituisce va in `HelixSR/backup` | **DLSS** (vanno bene anche FSR o XeSS) |
| **Metodo DLSS** (d, sperimentale) | DLSS | Il loader DLSS di HelixSR come `dxgi.dll` e HelixSR come `nvngx.dll` accanto al `.exe` del gioco | **DLSS** |

## Funzioni

### 1. Cerca i tuoi giochi Steam e i loro upscaler

- Al primo avvio vengono esaminate tutte le librerie Steam (anche quelle su altri dischi). Dopo aver installato giochi, fai clic su «⟳ Ricerca di nuovo i giochi Steam».
- Nella cartella di ogni gioco si cercano le DLL di FSR 3.1, DLSS, XeSS e FSR 2, e la cartella del suo `.exe` principale si ricava dalle informazioni di avvio di Steam (launcher e `*-Shipping.exe` di Unreal compresi).
- I giochi con **anti-cheat** (Easy Anti-Cheat, BattlEye) vengono segnalati.
- I nomi dei giochi seguono la lingua dell'interfaccia (nomi localizzati di Steam) e sono ordinati secondo quella lingua. I giochi che possono usare HelixSR vengono prima; il filtro «Giochi che possono usare HelixSR» è attivo per impostazione predefinita.

### 2. Installazione con un clic

- «Installa HelixSR» installa con il metodo predefinito; la freccia accanto propone gli altri. Ogni metodo indica cosa scegliere nel gioco.
- Prima di cambiare qualsiasi cosa, lo strumento controlla che la cartella di HelixSR sia pronta (rete creata) e che il gioco non sia in esecuzione.
- Il metodo DLSS spiega prima i suoi rischi e chiede conferma. Anche i giochi con anti-cheat chiedono conferma.
- Alla fine, il registro indica esattamente quali file sono stati sostituiti, dove sono conservati quelli del gioco e cosa scegliere nel gioco.

### 3. Cambiare metodo, aggiornare e riparare

- **Cambiare**: «Altro» → «Passa al …» rimuove prima il metodo attuale (rimettendo tutto a posto) e poi installa quello nuovo. Le tue impostazioni di HelixSR seguono il gioco.
- **Aggiornare**: quando la tua cartella di HelixSR contiene una versione più recente di quella di un gioco (nuova versione di HelixSR o rete creata di nuovo), il gioco mostra «↑ HelixSR … disponibile» e un pulsante «↑ Aggiorna»; «↑ Aggiorna tutti» aggiorna tutti i giochi in una volta.
- **Riparare**: un aggiornamento del gioco o «Verifica l'integrità dei file di gioco» in Steam possono rimettere i file del gioco sopra HelixSR. Il gioco spiega allora cosa è successo e mostra un pulsante «Ripara», che rimette HelixSR al suo posto e conserva i nuovi file del gioco come copia.
- Quando nei tuoi Scaricati (o in un altro posto abituale) compare una cartella di HelixSR più recente e pronta, lo strumento propone una volta di usarla.

### 4. Rimuovere

- «Rimuovi» toglie HelixSR e rimette ogni file che ha sostituito o spostato esattamente com'era.
- Le impostazioni di HelixSR del gioco (`helixsr.ini`) vengono mantenute, a meno che tu non spunti «Rimuovi anche le impostazioni di HelixSR di questo gioco».
- I file che hai messo tu nella cartella `my-fsr` del gioco non vengono mai cancellati.

### 5. Impostazioni di HelixSR senza modificare file

«⚙ Impostazioni» modifica l'`helixsr.ini` del gioco tramite un modulo. Sono proposte solo le impostazioni documentate nel README di HelixSR:

| Gruppo | Impostazione | Valori |
|---|---|---|
| Nitidezza | Filtro di nitidezza | Predefinito, Disattivato, NVIDIA, RCAS |
| | Intensità | 0.00 – 1.00 |
| | Segui il cursore di nitidezza del gioco | Predefinito, Sì, No |
| Upscaling (HelixSR 1.9.0+) | Rete int8 | Predefinito (automatico), Automatico, Attivato, Disattivato |
| | Passaggio finale in Ultra Prestazioni | Predefinito (Lanczos), Lanczos, EASU (FSR 1) |
| Compatibilità | Dimensione wave | Predefinito, 64, 32 |

«Predefinito» omette la riga, così HelixSR usa il proprio valore predefinito. I commenti e tutte le altre righe del file restano come sono. Il file viene scritto accanto alla DLL di HelixSR secondo il metodo del gioco (la cartella `HelixSR` del gioco, accanto alla DLL FSR del gioco o accanto al `.exe`).

### 6. Stato di HelixSR in tempo reale (cosa funziona davvero)

I giochi Steam in esecuzione vengono controllati ogni 3 secondi:

- Proton carica le DLL di Windows dai loro file, quindi lo strumento vede in `/proc/<pid>/maps` se il gioco **ha davvero caricato HelixSR** (e OptiScaler o il loader DLSS).
- HelixSR viene caricato solo quando il gioco usa l'upscaler. Per questo «HelixSR non ancora caricato» ti dice cosa scegliere nelle impostazioni grafiche del gioco.
- Viene letto l'`helixsr.log` della sessione corrente: sono mostrati la dimensione wave dei kernel della rete e le eventuali righe di errore. «Altro» → «Mostra helixsr.log» mostra il registro completo con un pulsante per copiarlo.
- Sulle GPU **RDNA 3 e successive**, nei giochi con il metodo OptiScaler, il README di HelixSR consiglia `WaveSize = 64` quando il registro indica wave32. Lo strumento lo rileva e propone «Imposta WaveSize = 64» con un clic.
- L'indicatore GPU in alto mostra la generazione della tua GPU (per esempio «AMD RDNA 3 (gfx1100)»).

### 7. Avviso all'avvio di un gioco

Se l'Assistente HelixSR è aperto quando parte un gioco con HelixSR, appena HelixSR viene caricato compare in basso a destra per circa 10 secondi una piccola scheda con versione, metodo e dimensione wave (una volta per avvio; i giochi già aperti prima dello strumento vengono saltati). Se HelixSR non è ancora caricato dopo 90 secondi, la scheda indica cosa scegliere nel gioco. L'avviso è una finestra X11 (XWayland) separata che non prende mai il focus e lascia passare i clic. Si disattiva con la casella nella barra degli strumenti. Non compare nella modalità Gioco di Steam Deck (gamescope).

### 8. Avviare giochi, cercare e filtrare

- Ogni riga ha un pulsante «▶ Avvia» (tramite `steam://rungameid/<AppID>`); mostra «In esecuzione» mentre il gioco è aperto.
- Cerca per nome del gioco (in qualsiasi lingua) o App ID. Filtri: giochi che possono usare HelixSR, installato, non installato, da aggiornare o riparare, in esecuzione, tutti i giochi.

### 9. Dodici lingue di interfaccia

台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी. Al primo avvio si usa la lingua del sistema; cambiala in alto a destra (effetto immediato, viene ricordata).

### 10. Pensato per la sicurezza

- Non si cambia nulla finché la cartella di HelixSR non è pronta o se il gioco è in esecuzione.
- Ogni file sostituito da HelixSR viene conservato (`*.original.dll` o `HelixSR/backup`), e ogni file copiato viene verificato byte per byte.
- Un `OptiScaler.ini` già presente viene salvato e ripristinato alla rimozione; una DLL FSR che hai sostituito a mano nella cartella `HelixSR` del gioco viene mantenuta negli aggiornamenti.
- Il metodo DLSS e i giochi con anti-cheat richiedono una conferma esplicita.

## Funziona insieme all'installazione di HelixSR

L'Assistente HelixSR scrive lo stesso registro di installazione (`helixsr-install.json`), le stesse copie e gli stessi nomi di file dell'installazione di HelixSR. Quindi:

- I giochi preparati con `helixsr-setup.sh` risultano installati nell'Assistente HelixSR, con il loro metodo, e lì si possono cambiare, aggiornare o rimuovere.
- I giochi preparati con l'Assistente HelixSR vengono riconosciuti dall'installazione di HelixSR e da `helixsr-uninstall.sh`, che possono aggiornarli o rimuoverli.

## Installare l'Assistente HelixSR

**AppImage (consigliato)**: include Python e Qt, non serve installare altro.

1. Scarica `HelixSR_Assistant-<versione>-x86_64.AppImage` dalla pagina [Releases](https://github.com/mosesmoon/helixsr-assistant/releases).
2. Rendilo eseguibile: clic destro sul file → Proprietà → Permessi, e attiva «Consenti l'esecuzione del file come programma» (la dicitura varia con il gestore di file).
3. Fai doppio clic per aprire l'Assistente HelixSR.

Oppure in un terminale:

```bash
chmod +x HelixSR_Assistant-*-x86_64.AppImage
./HelixSR_Assistant-*-x86_64.AppImage
```

Se non si avvia, al sistema potrebbe mancare FUSE; eseguilo allora con `./HelixSR_Assistant-*-x86_64.AppImage --appimage-extract-and-run`.

**Dai sorgenti**: richiede Python 3.11 o successivo e PyQt6 (Arch: `sudo pacman -S python-pyqt6`).

```bash
./helixsr-assistant    # eseguire direttamente
./install.sh           # installare in ~/.local/share/helixsr-assistant e aggiungere una voce al menu
```

## Limitazioni note

- **Solo giochi Steam.** Per i giochi di altri negozi usa l'installazione di HelixSR (trascina la cartella del gioco).
- HelixSR funziona solo nei giochi Direct3D 12. Un gioco elencato con una DLL DLSS o FSR può comunque usare Vulkan o Direct3D 11; in quel caso HelixSR non fa nulla.
- HelixSR cambia molto in fretta. L'Assistente HelixSR richiede HelixSR 1.8.0 o successivo ed è stato realizzato per la struttura delle versioni 1.8.x e 1.9.x; se una versione futura di HelixSR cambia il modo di preparare i giochi, usa l'installazione di HelixSR finché l'Assistente non viene aggiornato.
- L'avviso non compare nella modalità Gioco di Steam Deck (gamescope), e i giochi a schermo intero esclusivo Wayland nativo possono coprirlo.
- In tailandese, vietnamita, malese e hindi i menu contestuali sono in inglese (Qt non ha traduzioni ufficiali per queste lingue). Steam non ha nomi dei giochi in malese o hindi, quindi queste due lingue mostrano sempre i nomi originali.

## Dove sono salvati i dati

| Posizione | Contenuto |
|---|---|
| `~/.config/helixsr-assistant/state.json` | Stato proprio dell'Assistente HelixSR: cartella di HelixSR, cache dell'elenco dei giochi, lingua dell'interfaccia, impostazione dell'avviso |
| `<gioco>/…/HelixSR/helixsr-install.json`, accanto alla DLL FSR del gioco | Registro di installazione di HelixSR (condiviso con la sua installazione) |
| `<gioco>/…/helixsr.ini` | Impostazioni di HelixSR per quel gioco |
| `<gioco>/…/helixsr.log` | Ciò che HelixSR ha segnalato all'ultimo avvio del gioco |

## Licenze

L'Assistente HelixSR è uno strumento indipendente e non ufficiale. Non è affiliato né approvato dall'autore di HelixSR, da NVIDIA, AMD o dal progetto OptiScaler, e non contiene nessuno dei loro file. HelixSR è gratuito con la HelixSR Freeware License. Dopo l'installazione di HelixSR, le sue DLL contengono la rete di NVIDIA: l'Assistente HelixSR si limita a copiarle tra cartelle del tuo PC. Non condividerle né caricarle mai.
