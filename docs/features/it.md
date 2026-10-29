# Assistente Scaler — Guida alle funzioni

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · **Italiano** · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

L'**Assistente Scaler** è uno strumento desktop per Linux che ti fa scegliere l'upscaler di ogni gioco Steam — **DLSS 3.7 ([HelixSR](https://github.com/lonewolf0622/HelixSR))**, **FSR 4.1** (Exact o Lossy da [fsr4-shader-performance-overrides](https://github.com/zgauthier2000/fsr4-shader-performance-overrides), oppure quello di AMD sulle RX 9000) o **FSR 3** — e lo installa, cambia, aggiorna, ripara e rimuove con un clic. Mostra anche se l'upscaler funziona davvero mentre giochi.

## A chi serve

Mettere a mano un upscaler migliore in un gioco su Linux significa:

1. Scoprire quali upscaler ha il gioco (DLSS, XeSS, FSR 2, FSR 3.1), con quale API grafica disegna e dove si trova il suo `.exe` principale.
2. Mettere OptiScaler accanto al `.exe` con un nome di file che il gioco accetta, con le DLL FidelityFX necessarie, e modificare `OptiScaler.ini` per l'upscaler voluto.
3. Aggiungere `WINEDLLOVERRIDES` alle opzioni di avvio di Steam quando quel nome lo richiede, senza rovinare ciò che c'è già.
4. Scaricare la DLL FSR 4.1 giusta per la tua GPU, o configurare HelixSR come spiega il suo README.
5. Rifare tutto dopo ogni aggiornamento, e di nuovo quando un aggiornamento del gioco sovrascrive i file.

L'Assistente Scaler fa tutto questo da una finestra e conserva tutto ciò che sostituisce: rimuovendo, il gioco torna esattamente com'era.

## Le scelte per ogni gioco

L'API grafica e gli upscaler del gioco decidono cosa viene proposto. Il gioco deve avere già almeno un upscaler (DLSS, XeSS, FSR 2 o FSR 3.1): è quello che OptiScaler e HelixSR prendono in carico.

| Scelta | Il gioco deve avere | Cosa viene messo nella cartella del gioco | Da scegliere nel gioco |
|---|---|---|---|
| **DLSS 3.7 (HelixSR) · metodo FSR** | Direct3D 12, FSR 3.1 | La DLL FSR 3.1 del gioco viene sostituita da HelixSR (il file del gioco resta come `*.original.dll`) | AMD FSR |
| **DLSS 3.7 (HelixSR) · metodo OptiScaler** | Direct3D 12, DLSS, XeSS o FSR 2 | OptiScaler accanto al `.exe`, puntato a una cartella `HelixSR` | DLSS |
| **DLSS 3.7 (HelixSR) · metodo DLSS** (sperimentale) | Direct3D 12, DLSS | Il caricatore DLSS di HelixSR (`dxgi.dll`) e HelixSR come `nvngx.dll` | DLSS |
| **FSR 4.1 Exact** | uno dei quattro upscaler | OptiScaler accanto al `.exe`; le DLL FidelityFX e la DLL FSR 4.1 Exact in una cartella `ScalerAssistant` | DLSS, FSR o XeSS |
| **FSR 4.1 Lossy** | lo stesso | lo stesso, con la DLL FSR 4.1 Lossy | DLSS, FSR o XeSS |
| **FSR 4.1 Lossy2** | lo stesso | lo stesso, con la DLL FSR 4.1 Lossy2 | DLSS, FSR o XeSS |
| **FSR 4.1 (AMD)** — al posto di Exact / Lossy sulle RX 9000 (RDNA 4) | lo stesso | lo stesso, con la DLL FSR 4.1 di AMD | DLSS, FSR o XeSS |
| **FSR 3** | lo stesso | lo stesso; OptiScaler usa FSR 3.1.5 | DLSS, FSR o XeSS |

- **Exact** dà l'immagine dell'FSR 4.1 di AMD byte per byte, con shader più veloci. **Lossy** è ancora più veloce e cambia leggermente l'immagine; l'Assistente Scaler mostra una volta il suo `WARNING.txt` prima del primo uso. Nel dubbio, scegli Exact.
- **Lossy2** è Lossy con sei dei dodici strati della rete riaddestrati: il fogliame che ondeggia si avvicina all'immagine di AMD e ci sono meno pixel lucciola, ma segue più lentamente gli schiarimenti e in Ultra Performance è uguale a Lossy. È offerto accanto a Lossy per confrontarli e mostra una volta il proprio `WARNING.txt`.
- HelixSR funziona solo nei giochi **Direct3D 12**, quindi DLSS 3.7 è proposto solo lì. FSR 4.1 e FSR 3 funzionano anche nei giochi **Direct3D 11 e Vulkan**: FSR 3 in modo nativo, FSR 4.1 tramite il percorso Direct3D 12 di OptiScaler (meno testato dei giochi Direct3D 12).
- Fai clic su **«Scegli upscaler»** nella riga del gioco (o **«Upscaler»** quando ce n'è già uno): DLSS 3.7 (HelixSR) apre un sottomenu con i suoi metodi; la scelta attuale è spuntata. Cambiando, prima si rimuove l'attuale e tutto torna a posto.

## Prima di iniziare

- **FSR 4.1 e FSR 3** non richiedono altro: la prima volta l'Assistente Scaler chiede se scaricare OptiScaler e le DLL FSR 4.1 per la tua GPU (vedi «Download»).
- **DLSS 3.7** richiede HelixSR, che l'Assistente Scaler non include. Scarica HelixSR 1.8.0 o successivo dai suoi [GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases), estrailo in una cartella che conservi ed esegui lì una volta `./helixsr-setup.sh` (crea la rete di HelixSR sul tuo PC; quando chiede dei giochi puoi rispondere `n`). L'etichetta **HelixSR** in alto lo spiega; una cartella HelixSR configurata nella home, Scaricati, Scrivania o Games viene trovata da sola.
  Più semplice: premi **Scarica e compila HelixSR** in quella finestra (HelixSR 2.0 o successivo); Scaler Assistant fa tutto questo per te, senza terminale.
- I giochi girano con **Proton**. HelixSR è fatto per GPU AMD (RDNA 1 e successive). FSR 4.1 Exact / Lossy sono fatti per Radeon RX 7000 / RX 6000 e grafica Radeon integrata (anche Steam Deck); altre GPU dovrebbero eseguirli, ma l'autore non le ha testate. FSR 4.1 non funziona sulle GPU Radeon RX 5000 (RDNA 1) (ogni versione mostra solo un'immagine nera), quindi l'Assistente Scaler lo mostra in grigio su queste schede; FSR 3 e DLSS 3.7 (HelixSR) restano disponibili.

## Funzioni

### 1. Esamina i tuoi giochi Steam

- Al primo avvio vengono esaminate tutte le librerie Steam (anche su altri dischi). Dopo aver installato giochi fai clic su «⟳ Riesamina i giochi Steam».
- Per ogni gioco: le DLL di upscaling, la cartella del `.exe` principale (dalle informazioni di avvio di Steam; launcher e `*-Shipping.exe` di Unreal gestiti), l'**API grafica** (letta dalla tabella di importazione del `.exe`: DX12, DX11 o Vulkan) e se ha un **anti-cheat** (Easy Anti-Cheat, BattlEye).
- I nomi seguono la lingua dell'interfaccia (nomi localizzati di Steam). I giochi che si possono scalare vengono prima.

### 2. Un nome di file per OptiScaler che funziona nel gioco

Il gioco carica OptiScaler come DLL di sistema accanto al suo `.exe`. Il nome viene scelto così:

1. quello che hai scelto per il gioco («Altro» → «Nome del file di OptiScaler…»),
2. il nome di un OptiScaler già presente,
3. il nome che l'[elenco di compatibilità di OptiScaler](https://github.com/optiscaler/OptiScaler/wiki) indica per il gioco (per esempio `d3d12.dll` o `winmm.dll`),
4. `winmm.dll` per i giochi Vulkan,
5. un altro nome libero (`winmm.dll`, `version.dll`, …) quando il gioco o un'altra mod (per esempio ReShade) ha già un `dxgi.dll`, o quando le tue opzioni di avvio fissano quel nome sulla versione integrata,
6. altrimenti `dxgi.dll`.

Un file già presente non viene mai sovrascritto: va in `ScalerAssistant/backup` (`HelixSR/backup` per DLSS 3.7) e torna alla rimozione.

### 3. Opzioni di avvio di Steam: solo il necessario, le tue restano come sono

Con Proton, `dxgi.dll` e `d3d12.dll` si caricano senza altro. Ogni altro nome richiede `WINEDLLOVERRIDES="<nome>=n,b"` nelle opzioni di avvio, e l'Assistente Scaler lo aggiunge per te:

- **Viene inserita solo quella voce.** Se hai già `WINEDLLOVERRIDES`, al suo interno viene aggiunto `;winmm=n,b`; altrimenti si mette davanti `WINEDLLOVERRIDES="winmm=n,b"` (con `%command%` se mancava). Nient'altro cambia. Esempio: `-dx12 %command%` diventa `WINEDLLOVERRIDES="winmm=n,b" -dx12 %command%`.
- **Viene tolta solo quella voce** quando OptiScaler viene rimosso o rinominato. Se nel frattempo non hai cambiato le opzioni, tornano esattamente com'erano; altrimenti si toglie solo il testo inserito e le tue modifiche restano.
- Una voce che avevi già per quel nome non viene toccata né tolta in seguito. Se le tue opzioni impostano quel nome sulla versione integrata di Wine, l'Assistente Scaler usa un altro nome invece di cambiare la tua impostazione.
- Se la voce sparisce in seguito, il gioco mostra «Opzione di avvio mancante» e «Ripara» la aggiunge di nuovo.
- Con Steam aperto, le opzioni vengono cambiate tramite Steam stesso quando la sua porta di debug è disponibile (come usa Decky Loader). Altrimenti l'Assistente Scaler propone di chiudere Steam, scrivere la modifica e riaprirlo, prima di toccare qualsiasi file del gioco.

### 4. Download (FSR 4.1 e FSR 3)

Fai clic sull'etichetta **OptiScaler** in alto (o su quella della GPU):

- **OptiScaler 0.9.4** (con le DLL FidelityFX di AMD: FSR 3 e l'FSR 4.1 di AMD, più fakenvapi) e **FSR 4.1 Exact / Lossy / Lossy2** nella versione per la tua GPU: schede RX 7000, schede RX 6000, grafica RDNA 3 integrata nel processore (anche GeForce, Intel Arc e altre GPU), oppure Steam Deck e grafica RDNA 2 integrata nel processore. Ogni versione funziona su tutte; quella per la tua GPU è la più veloce. Se un gioco si chiude con Exact, scegli una versione per grafica integrata.
- Non si scarica nulla senza il tuo consenso. Ogni download è una versione fissa verificata per dimensione e SHA-256 prima dell'estrazione; si tengono solo i file che servono ai giochi, in `~/.local/share/scaler-assistant/components/`.
- **Versione di FSR 4.1**: automatica in base alla GPU (RX 9000 / RDNA 4 → FSR 4.1 di AMD, grafica integrata e Steam Deck → versione integrata, altre GPU → versione per schede grafiche), oppure scelta a mano. Su RDNA 4 le DLL modificate non vengono mai usate. Sulle altre GPU OptiScaler viene impostato sul modello INT8 di FSR 4.
- «Rimuovi download» li elimina; i giochi tengono le loro copie.

### 5. Cosa cambia in OptiScaler.ini

Solo le righe necessarie, nella loro sezione; tutte le altre righe e commenti restano:

| Chiave | FSR 4.1 | FSR 3 |
|---|---|---|
| `Dx12Upscaler` | `fsr31` | `fsr31` |
| `Dx11Upscaler`, `VulkanUpscaler` | `fsr31_12` (tramite Direct3D 12) | `fsr31` (nativo) |
| `UpscalerIndex` | `0` (FSR 4) | `1` (FSR 3.1.5) |
| `Fsr4Update` | `true` | `false` |
| `Fsr4ForceEnableInt8` | `true` prima di RDNA 4 | `auto` |
| `FfxDx12Path`, `FfxDx12SRPath`, `FfxDx12FGPath`, `FfxVkPath` | le DLL nella cartella `ScalerAssistant` del gioco | lo stesso |

Un `OptiScaler.ini` già presente viene prima salvato e rimesso al suo posto alla rimozione.

### 6. Cambiare, aggiornare, riparare, rimuovere

- **Cambia** dal menu dell'upscaler: prima si rimuove la scelta attuale, poi si installa la nuova. Tra FSR 4.1 Exact, Lossy e FSR 3 cambiano solo la DLL FSR e `OptiScaler.ini`.
- **Aggiorna**: un gioco mostra «↑ HelixSR … disponibile» quando la tua cartella HelixSR ha una versione più recente, o «↑ Download più recente disponibile» quando c'è un download OptiScaler / FSR 4.1 più recente (o un'altra versione di FSR 4.1). «↑ Aggiorna tutto» aggiorna tutti i giochi.
- **Ripara**: un aggiornamento del gioco o «Verifica integrità dei file» può rimettere i file del gioco. Il gioco mostra cosa è successo e «Ripara» rimette l'upscaler, tenendo i nuovi file del gioco come copia.
- **Rimuovi** rimette ogni file sostituito o spostato e toglie la voce dalle opzioni di avvio.

### 7. Impostazioni di HelixSR senza modificare file

Con DLSS 3.7, «⚙ Impostazioni» modifica l'`helixsr.ini` del gioco con un modulo (nitidezza, rete int8, passaggio finale in Ultra Prestazioni, dimensione wave). «Predefinito» omette la riga; le altre righe e commenti restano.

### 8. Stato in tempo reale e avviso in sovrimpressione

- I giochi Steam in esecuzione vengono controllati ogni 3 secondi: `/proc/<pid>/maps` mostra se il gioco **ha davvero caricato** HelixSR o la DLL FSR (e OptiScaler o il caricatore DLSS). Nulla viene caricato finché il gioco non usa l'upscaler, quindi «non ancora caricato» ti dice cosa scegliere nel gioco.
- Con HelixSR, l'`helixsr.log` della sessione mostra la dimensione wave e gli errori; su RDNA 3 e successive con il metodo OptiScaler viene proposto «Imposta WaveSize = 64» quando il registro indica wave32.
- Il pannello dei dettagli di un gioco (il pulsante ⌄ della sua scheda) offre «Mostra …log» per `helixsr.log` o `OptiScaler.log`, la cartella del gioco, il nome del file di OptiScaler e, per DLSS 3.7, «⚙ Impostazioni».
- All'avvio di un gioco, una piccola scheda in basso a destra mostra il risultato per circa 10 secondi (o un suggerimento dopo 90 secondi). È una finestra X11 separata che non prende mai il focus; si disattiva con l'interruttore della barra degli strumenti.

### 9. Avviare, cercare, filtrare, lingue

- «▶ Avvia» apre il gioco tramite Steam. Cerca per nome (qualsiasi lingua) o App ID; filtri: giochi che si possono scalare, upscaler installato, nessun upscaler per ora, da aggiornare o riparare, in esecuzione, tutti i giochi.
- 12 lingue di interfaccia: 台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी.

### 10. Progettato per la sicurezza

- Niente cambia mentre il gioco è in esecuzione; download e cartella HelixSR vengono verificati prima di toccare qualsiasi file.
- Ogni file sostituito viene conservato, ogni copia verificata byte per byte, e le opzioni di avvio cambiano solo per la voce descritta sopra.
- Il metodo DLSS, FSR 4.1 Lossy e i giochi con anti-cheat chiedono prima conferma. Non usare mai un upscaler modificato nei giochi online: l'anti-cheat può considerarlo manomissione.

### 11. Aspetto

- Nello stile di MAKO Assistant («Liquid Glass»): una scheda per gioco con la copertina Steam, un'etichetta di stato, ciò che il gioco offre e, mentre è in esecuzione, ciò che è davvero caricato. Il pulsante ⌄ apre i dettagli (API grafica, upscaler, cartella dell'`.exe`, nome di OptiScaler, opzioni di avvio) e le azioni meno frequenti.
- I pulsanti sono cristallo trasparente in rilievo: una tinta leggera con un bordo sottile, un riflesso curvo sulla metà superiore, un bagliore lungo il bordo inferiore e un'ombra morbida sotto, tutto a strati traslucidi piatti, senza sfumature. Le manopole degli interruttori sporgono allo stesso modo; il tema scelto è un cristallo in rilievo in una pista incassata. Turchese installa, blu cambia, ambra aggiorna, rosso rimuove.
- Tema scuro, chiaro o automatico (segue il desktop). Il registro attività è il cassetto in fondo alla finestra.

## HelixSR 2.0 e la GPU

- **Scarica e compila HelixSR in un passo**: «Scarica e compila HelixSR» (nella finestra di HelixSR e nel plugin per Steam Deck) scarica l'HelixSR più recente (2.0 o successivo) dalle release GitHub, verificato con SHA-256, in `~/.local/share/scaler-assistant/helixsr` e lo compila su questo PC con il programma di compilazione di HelixSR (`setup/helixsr_setup.py`, eseguito così com'è), come fa l'app di HelixSR: senza terminale e senza il passaggio dei giochi. Procura ciò che serve alla compilazione: un Python con numpy (un Python 3.14 portatile quando quello di sistema non sa estrarre il pacchetto zstd di NVIDIA, così la generazione di frame non richiede `zstd`) e il DirectX Shader Compiler di Microsoft, eseguito tramite Proton di Steam o Wine. I file di NVIDIA vengono scaricati solo dopo il tuo consenso nell'app; il risultato resta sul tuo PC. In Flatpak la compilazione gira sull'host. Rieseguendolo si compila solo ciò che manca; una release più recente sostituisce quella scaricata prima.
- **HelixSR 2.0 e successive** tengono la DLL costruita in `HelixSR-fsrfg` e offrono due metodi: **HelixSR Scaler** (l'OptiScaler di HelixSR accanto all'`.exe`: scegli DLSS nel gioco; anche giochi DX11 e Vulkan) e il **metodo FSR** (FSR drop-in). L'Assistente Scaler li installa con l'installer della tua cartella HelixSR (`setup/helixsr_bridge.py`, quello usato dall'app di HelixSR), così il setup di HelixSR, la sua app e l'Assistente Scaler riconoscono, aggiornano e rimuovono le installazioni degli altri. Il nome del file lo sceglie sempre l'Assistente Scaler, che aggiunge l'opzione di avvio quando serve. I giochi configurati con un metodo precedente passano a HelixSR Scaler all'aggiornamento. Le cartelle HelixSR 1.8 / 1.9 mantengono i loro tre metodi.
- **Generazione di frame HelixSR** (HelixSR 2.0): nei giochi DirectX 12 con DLSS Frame Generation (il `sl.dlss_g.dll` di Streamline), un gioco con HelixSR Scaler ha un interruttore «Generazione di frame HelixSR» sulla sua scheda (e nel plugin per Steam Deck). Usa l'installer di HelixSR (`scaler-fg`), che cambia solo la scelta `[FrameGen]` di OptiScaler.ini; poi attiva DLSS Frame Generation nel gioco. Serve la generazione di frame creata da `./helixsr-setup.sh` (scarica i file DLSS Frame Generation di NVIDIA); fino ad allora l'interruttore è grigio con il motivo. Le nuove installazioni la lasciano disattivata; un aggiornamento o un nuovo nome file di OptiScaler mantiene lo stato. Gli altri giochi DX12 possono ancora scegliere la generazione di frame AMD FSR o XeSS nel menu di HelixSR Scaler (Ins); i giochi DX11 / Vulkan e la via FSR hanno solo l'upscaling.
- **HelixSR 3.0**: la DLL compilata è `HelixSR/helixsr.dll` (l'upscaler DLSS di HelixSR Scaler, «HLX DLSS») e la via FSR installa **HLX FSR 4**, la pipeline FSR 4 di HelixSR, che il setup di HelixSR compila dal file driver FSR 4 di AMD (scarica da AMD circa 420 MB del suo pacchetto driver; «Scarica e compila HelixSR» lo chiede prima e porta anche il secondo compilatore di shader, DXC 1.9.2609). L'Assistente Scaler installa, aggiorna, cambia e rimuove entrambe le vie tramite l'installer della release, come con 2.0; i giochi configurati con 2.0 passano da `HelixSR-fsrfg` a `HelixSR` con l'aggiornamento. HelixSR 3.0 non ha generazione di frame, quindi l'interruttore qui sopra non compare con esso; la generazione di frame AMD FSR e XeSS resta nel menu di HelixSR Scaler.
- **Versioni precedenti di HelixSR**: 1.8.x offre tutti e tre i metodi (FSR, OptiScaler, DLSS). HelixSR 1.9.0 – 1.9.3 contengono solo i file del metodo FSR, quindi i metodi OptiScaler e DLSS sono in grigio («richiede HelixSR 1.8 o 2.0»); i giochi senza FSR 3.1 richiedono HelixSR 2.0 (HelixSR Scaler). Le versioni precedenti alla 1.8.0 non sono supportate.
- **Metodo DLSS solo con una GeForce**: con una GPU AMD o Intel i giochi non offrono DLSS, quindi il metodo DLSS (HelixSR 1.x) è in grigio con il motivo.
- **FSR 4.1 Lossy consigliato** con grafica integrata (Steam Deck, ROG Ally Z1 / Z2, Ryzen AI MAX) e GPU Intel: indicato «★ Consigliato» solo tra le scelte FSR 4.1.

## Funziona con l'installazione di HelixSR

Con DLSS 3.7, l'Assistente Scaler scrive lo stesso registro di installazione (`helixsr-install.json`), le stesse copie e gli stessi nomi dell'installazione di HelixSR: `helixsr-setup.sh` / `helixsr-uninstall.sh` e l'Assistente Scaler riconoscono i giochi l'uno dell'altro. L'installazione di HelixSR scambia la DLL FSR nella cartella `ScalerAssistant` di un gioco per la DLL FSR 3.1 del gioco e può sostituirla con HelixSR; l'Assistente Scaler segnala allora il gioco come da riparare e «Ripara» toglie HelixSR. Per usare DLSS 3.7 in un gioco del genere, sceglilo nell'Assistente Scaler.

## Plugin per Steam Deck (Decky Loader)

Lo stesso programma per la modalità Gioco, come plugin di [Decky Loader](https://decky.xyz) nel menu di accesso rapido.

- **Giochi**: i giochi che si possono scalare, prima quelli in esecuzione, ognuno con la sua etichetta di stato e, mentre è in esecuzione, ciò che è davvero caricato. Scegli un gioco per selezionare DLSS 3.7 (HelixSR, ogni metodo), FSR 4.1 Exact / Lossy o FSR 3, oppure per aggiornarlo, ripararlo, rimuoverlo, cambiare il nome del file di OptiScaler o leggerne il registro. Prima arrivano le stesse domande dell'app desktop: download, avviso Lossy, metodo DLSS e anti-cheat.
- **Configurazione**: la cartella di HelixSR (selettore di file), i download e la build di FSR 4.1 (la Steam Deck riceve quella per grafica integrata), una notifica all'avvio di un gioco (dice se l'upscaler è caricato) e la lingua (di default quella di Steam).
- Condivide `state.json`, i download e le voci delle opzioni di avvio con l'app desktop: i giochi configurati in uno compaiono nell'altro. Le opzioni di avvio vengono scritte subito tramite Steam.
- Non nel plugin: il modulo delle impostazioni di HelixSR (usa l'app desktop) e il `helixsr-setup.sh` di HelixSR, da eseguire una volta in modalità Desktop.
- Nel plugin, **Scarica e compila HelixSR** scarica e compila HelixSR 2.0 o successivo anche in modalità Gioco (richiede alcuni minuti).

Installazione: installa Decky Loader sulla Steam Deck, scarica `Scaler_Assistant-Decky-<versione>.zip` dalla pagina [Releases](https://github.com/mosesmoon/scaler-assistant/releases), poi nelle impostazioni di Decky → Sviluppatore (attiva prima la modalità sviluppatore in Generale) → «Install Plugin from ZIP File».

## Installare l'Assistente Scaler

**AppImage (consigliato)**: Python, Qt e 7-Zip sono inclusi.

1. Scarica `Scaler_Assistant-<versione>-x86_64.AppImage` dalla pagina [Releases](https://github.com/mosesmoon/scaler-assistant/releases).
2. Rendilo eseguibile: clic destro → Proprietà → Permessi → «Consenti l'esecuzione del file come programma» (il testo cambia secondo il gestore di file).
3. Fai doppio clic.

```bash
chmod +x Scaler_Assistant-*-x86_64.AppImage
./Scaler_Assistant-*-x86_64.AppImage
```

Se non si avvia, forse manca FUSE; eseguilo con `--appimage-extract-and-run`.

**Installer unico (.bin)**: `Scaler_Assistant-<versione>-x86_64.bin` installa la stessa app inclusa solo per il tuo utente (senza root né FUSE) in `~/.local/opt/scaler-assistant`, con il comando `scaler-assistant` e una voce di menu. **Flatpak**: `Scaler_Assistant-<versione>-x86_64.flatpak` è un pacchetto in un solo file sul runtime Freedesktop 25.08 (scaricato da Flathub all'installazione). Può leggere la tua cartella home e altri dischi (schede SD in `/run/media`) e vede i processi di Steam e dei giochi tramite `flatpak-spawn --host`.

```bash
sh Scaler_Assistant-*-x86_64.bin                # install / installa
sh Scaler_Assistant-*-x86_64.bin --uninstall    # remove / rimuovi
flatpak install --user Scaler_Assistant-*-x86_64.flatpak
flatpak run io.github.mosesmoon.ScalerAssistant
```

**Dal codice sorgente**: Python 3.11+ e PyQt6 (Arch: `sudo pacman -S python-pyqt6`), più 7-Zip o bsdtar per estrarre OptiScaler (`sudo pacman -S 7zip`).

```bash
./scaler-assistant     # eseguire direttamente
./install.sh           # installare in ~/.local/share/scaler-assistant e aggiungere al menu
```

## Limiti noti

- **Solo giochi Steam.** I metodi FSR 4.1 / FSR 3 sono stati verificati file per file con OptiScaler 0.9.4; ogni gioco si comporta in modo diverso: in caso di problemi consulta l'elenco di compatibilità di OptiScaler o scegli un altro nome di file per OptiScaler.
- FSR 4.1 nei giochi Direct3D 11 e Vulkan passa per il percorso Direct3D 12 di OptiScaler ed è meno testato.
- HelixSR cambia rapidamente. L'Assistente Scaler richiede HelixSR 1.8.0 o successivo e segue la struttura di 1.8.x / 1.9.x / 2.0.x / 3.0.x / 3.1.x.
- L'avviso in sovrimpressione non compare nella modalità Gioco della Steam Deck (gamescope). Il plugin Decky mostra invece una notifica di Steam.
- In thailandese, vietnamita, malese e hindi i menu contestuali sono in inglese (Qt non ha traduzioni ufficiali). Steam non ha nomi di giochi in malese né in hindi.

## Dove sono salvati i dati

| Posizione | Contenuto |
|---|---|
| `~/.config/scaler-assistant/state.json` | Stato dell'Assistente Scaler: cartella HelixSR, elenco dei giochi, lingua, versione di FSR 4.1, nomi di OptiScaler scelti, voci aggiunte alle opzioni di avvio (prese una volta dall'Assistente HelixSR) |
| `~/.local/share/scaler-assistant/components/` | I file OptiScaler e FSR 4.1 scaricati |
| `~/homebrew/plugins/scaler-assistant/` | Il plugin Decky sulla Steam Deck (usa lo stesso stato e gli stessi download di sopra) |
| `<gioco>/…/ScalerAssistant/` | FSR 4.1 / FSR 3: DLL FidelityFX, `scaler-install.json`, `backup/` |
| `<gioco>/…/HelixSR/helixsr-install.json`, accanto alla DLL FSR del gioco | DLSS 3.7: registro di installazione di HelixSR (condiviso con la sua installazione) |
| `<gioco>/…/helixsr.ini`, `helixsr.log`, `OptiScaler.ini`, `OptiScaler.log` | Impostazioni e registri |

## Licenze

L'Assistente Scaler è uno strumento indipendente e non ufficiale, non affiliato né approvato dall'autore di HelixSR, NVIDIA, AMD, dal progetto OptiScaler o dal progetto fsr4-shader-performance-overrides, e non contiene nessuno dei loro file. Su tua richiesta scarica OptiScaler (GPL-3.0; fakenvapi MIT; DLL FidelityFX di AMD sotto licenza AMD) e le DLL FSR 4.1 (GPL-2.0-or-later, DLL AMD modificate con l'avviso di AMD) dai loro GitHub Releases. L'AppImage include il `7zzs` di 7-Zip (GNU LGPL con la restrizione unRAR, BSD; licenza inclusa). HelixSR è gratuito con la HelixSR Freeware License; dopo la sua installazione le sue DLL contengono la rete di NVIDIA, quindi l'Assistente Scaler le copia solo tra cartelle del tuo PC. Non condividerle né caricarle mai. Il plugin Decky include lo stesso `7zzs`.
