# Asistente de Scaler — Guía de funciones

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · **Español** · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

El **Asistente de Scaler** es una herramienta de escritorio para Linux que te permite elegir el escalador de cada juego de Steam — **DLSS 3.7 ([HelixSR](https://github.com/lonewolf0622/HelixSR))**, **FSR 4.1** (Exact o Lossy de [fsr4-shader-performance-overrides](https://github.com/zgauthier2000/fsr4-shader-performance-overrides), o el propio de AMD en RX 9000) o **FSR 3** — e instalarlo, cambiarlo, actualizarlo, repararlo y quitarlo con un clic. También muestra si el escalador funciona de verdad mientras juegas.

## Para quién es

Poner a mano un escalador mejor en un juego en Linux significa:

1. Averiguar qué escaladores trae el juego (DLSS, XeSS, FSR 2, FSR 3.1), con qué API gráfica renderiza y dónde está su `.exe` principal.
2. Poner OptiScaler junto al `.exe` con un nombre de archivo que el juego acepte, con las DLL FidelityFX necesarias, y editar `OptiScaler.ini` para el escalador que quieres.
3. Añadir `WINEDLLOVERRIDES` a las opciones de lanzamiento de Steam cuando ese nombre lo necesita, sin romper lo que ya hay.
4. Descargar la DLL de FSR 4.1 adecuada para tu GPU, o configurar HelixSR como explica su README.
5. Repetirlo tras cada actualización, y otra vez cuando una actualización del juego sobrescribe tus archivos.

El Asistente de Scaler hace todo esto desde una ventana y guarda todo lo que reemplaza, así que al quitarlo el juego queda exactamente como estaba.

## Las opciones de cada juego

La API gráfica y los escaladores del juego deciden qué se ofrece. El juego debe traer al menos un escalador (DLSS, XeSS, FSR 2 o FSR 3.1): es lo que OptiScaler y HelixSR toman.

| Opción | El juego necesita | Qué se pone en la carpeta del juego | Elegir en el juego |
|---|---|---|---|
| **DLSS 3.7 (HelixSR) · método FSR** | Direct3D 12, FSR 3.1 | La DLL de FSR 3.1 del juego se reemplaza por HelixSR (el archivo del juego se guarda como `*.original.dll`) | AMD FSR |
| **DLSS 3.7 (HelixSR) · método OptiScaler** | Direct3D 12, DLSS, XeSS o FSR 2 | OptiScaler junto al `.exe`, apuntando a una carpeta `HelixSR` | DLSS |
| **DLSS 3.7 (HelixSR) · método DLSS** (experimental) | Direct3D 12, DLSS | El cargador DLSS de HelixSR (`dxgi.dll`) y HelixSR como `nvngx.dll` | DLSS |
| **FSR 4.1 Exact** | cualquiera de los cuatro escaladores | OptiScaler junto al `.exe`; las DLL FidelityFX y la DLL de FSR 4.1 Exact en una carpeta `ScalerAssistant` | DLSS, FSR o XeSS |
| **FSR 4.1 Lossy** | lo mismo | lo mismo, con la DLL de FSR 4.1 Lossy | DLSS, FSR o XeSS |
| **FSR 4.1 (AMD)** — en lugar de Exact / Lossy en RX 9000 (RDNA 4) | lo mismo | lo mismo, con la DLL de FSR 4.1 propia de AMD | DLSS, FSR o XeSS |
| **FSR 3** | lo mismo | lo mismo; OptiScaler usa FSR 3.1.5 | DLSS, FSR o XeSS |

- **Exact** da la imagen de FSR 4.1 de AMD byte a byte, con shaders más rápidos. **Lossy** es aún más rápido y cambia ligeramente la imagen; el Asistente de Scaler muestra una vez su `WARNING.txt` antes del primer uso. Si dudas, elige Exact.
- HelixSR solo funciona en juegos **Direct3D 12**, así que DLSS 3.7 solo se ofrece ahí. FSR 4.1 y FSR 3 también funcionan en juegos **Direct3D 11 y Vulkan**: FSR 3 de forma nativa, FSR 4.1 a través de la ruta Direct3D 12 de OptiScaler (menos probado que en juegos Direct3D 12).
- Haz clic en **«Elegir escalador»** en la fila del juego (o **«Escalador»** cuando ya hay uno): DLSS 3.7 (HelixSR) abre un submenú con sus métodos; la elección actual está marcada. Al cambiar, primero se quita la actual y todo vuelve a su sitio.

## Antes de empezar

- **FSR 4.1 y FSR 3** no necesitan nada más: la primera vez, el Asistente de Scaler pregunta si descargar OptiScaler y las DLL de FSR 4.1 para tu GPU (ver «Descargas»).
- **DLSS 3.7** necesita HelixSR, que el Asistente de Scaler no incluye. Descarga HelixSR 1.8.0 o posterior de sus [GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases), extráelo en una carpeta que conserves y ejecuta allí una vez `./helixsr-setup.sh` (crea la red de HelixSR en tu PC; cuando pregunte por los juegos puedes responder `n`). La etiqueta **HelixSR** de arriba lo explica; una carpeta de HelixSR configurada en tu carpeta personal, Descargas, Escritorio o Games se encuentra sola.
- Los juegos se ejecutan con **Proton**. HelixSR está hecho para GPU AMD (RDNA 1 y posteriores). FSR 4.1 Exact / Lossy están hechos para Radeon RX 7000 / RX 6000 y gráficas Radeon integradas (incluida Steam Deck); otras GPU deberían ejecutarlos, pero su autor no las ha probado.

## Funciones

### 1. Explora tus juegos de Steam

- Al primer inicio se exploran todas las bibliotecas de Steam (también en otros discos). Pulsa «⟳ Volver a explorar los juegos de Steam» tras instalar juegos.
- Para cada juego: las DLL de escalado que trae, la carpeta de su `.exe` principal (según la información de lanzamiento de Steam; lanzadores y `*-Shipping.exe` de Unreal incluidos), su **API gráfica** (leída de la tabla de importación del `.exe`: DX12, DX11 o Vulkan) y si tiene **antitrampas** (Easy Anti-Cheat, BattlEye).
- Los nombres siguen el idioma de la interfaz (nombres localizados de Steam). Los juegos que se pueden escalar van primero.

### 2. Un nombre de archivo de OptiScaler que funcione en el juego

El juego carga OptiScaler como una DLL del sistema junto a su `.exe`. El nombre se elige así:

1. el que elegiste para el juego («Más» → «Nombre de archivo de OptiScaler…»),
2. el nombre de un OptiScaler que ya esté,
3. el nombre que da la [lista de compatibilidad de OptiScaler](https://github.com/optiscaler/OptiScaler/wiki) para el juego (por ejemplo `d3d12.dll` o `winmm.dll`),
4. `winmm.dll` en juegos Vulkan,
5. otro nombre libre (`winmm.dll`, `version.dll`, …) cuando el juego u otro mod (ReShade, por ejemplo) ya tiene un `dxgi.dll`, o cuando tus opciones de lanzamiento fijan ese nombre a la versión integrada,
6. si no, `dxgi.dll`.

Un archivo que ya está nunca se sobrescribe: va a `ScalerAssistant/backup` (`HelixSR/backup` en DLSS 3.7) y vuelve al quitarlo.

### 3. Opciones de lanzamiento de Steam: solo lo necesario, las tuyas se quedan como están

En Proton, `dxgi.dll` y `d3d12.dll` se cargan sin nada más. Cualquier otro nombre necesita `WINEDLLOVERRIDES="<nombre>=n,b"` en las opciones de lanzamiento, y el Asistente de Scaler lo añade por ti:

- **Solo se inserta esa entrada.** Si ya tienes `WINEDLLOVERRIDES`, se añade `;winmm=n,b` dentro; si no, se pone `WINEDLLOVERRIDES="winmm=n,b"` delante (con `%command%` si faltaba). Nada más cambia. Ejemplo: `-dx12 %command%` pasa a `WINEDLLOVERRIDES="winmm=n,b" -dx12 %command%`.
- **Solo se quita esa entrada** cuando OptiScaler se elimina o se renombra. Si no cambiaste las opciones entretanto, vuelven exactamente a como estaban; si las cambiaste, solo se quita el texto insertado y tus cambios se mantienen.
- Una entrada que ya tenías para ese nombre no se toca ni se quita después. Si tus opciones ponen ese nombre en la versión integrada de Wine, el Asistente de Scaler usa otro nombre en lugar de cambiar tu ajuste.
- Si la entrada desaparece más tarde, el juego muestra «Falta la opción de lanzamiento» y «Reparar» la vuelve a añadir.
- Con Steam abierto, las opciones se cambian a través del propio Steam cuando su puerto de depuración está disponible (como usa Decky Loader). Si no, el Asistente de Scaler ofrece cerrar Steam, escribir el cambio y volver a abrirlo, antes de tocar ningún archivo del juego.

### 4. Descargas (FSR 4.1 y FSR 3)

Haz clic en la etiqueta **OptiScaler** de arriba (o la de la GPU):

- **OptiScaler 0.9.4** (con las DLL FidelityFX de AMD: FSR 3 y el FSR 4.1 de AMD, más fakenvapi) y **FSR 4.1 Exact / Lossy** en la versión para tarjetas gráficas o para gráfica integrada.
- No se descarga nada sin tu permiso. Cada descarga es una versión fija comprobada por tamaño y SHA-256 antes de descomprimirla; solo se guardan los archivos que necesitan los juegos, en `~/.local/share/scaler-assistant/components/`.
- **Versión de FSR 4.1**: automática según tu GPU (RX 9000 / RDNA 4 → FSR 4.1 de AMD, gráfica integrada y Steam Deck → versión integrada, otras GPU → versión para tarjetas gráficas), o elegida a mano. En RDNA 4 nunca se usan las DLL modificadas. En las demás GPU, OptiScaler se configura con el modelo INT8 de FSR 4.
- «Eliminar descargas» las borra; los juegos conservan sus copias.

### 5. Qué cambia en OptiScaler.ini

Solo las líneas necesarias, en su propia sección; todas las demás líneas y comentarios se conservan:

| Clave | FSR 4.1 | FSR 3 |
|---|---|---|
| `Dx12Upscaler` | `fsr31` | `fsr31` |
| `Dx11Upscaler`, `VulkanUpscaler` | `fsr31_12` (a través de Direct3D 12) | `fsr31` (nativo) |
| `UpscalerIndex` | `0` (FSR 4) | `1` (FSR 3.1.5) |
| `Fsr4Update` | `true` | `false` |
| `Fsr4ForceEnableInt8` | `true` antes de RDNA 4 | `auto` |
| `FfxDx12Path`, `FfxDx12SRPath`, `FfxDx12FGPath`, `FfxVkPath` | las DLL de la carpeta `ScalerAssistant` del juego | lo mismo |

Un `OptiScaler.ini` que ya existía se guarda primero y se restaura al quitarlo.

### 6. Cambiar, actualizar, reparar, quitar

- **Cambiar** desde el menú del escalador: primero se quita la opción actual y luego se instala la nueva. Entre FSR 4.1 Exact, Lossy y FSR 3 solo cambian la DLL de FSR y `OptiScaler.ini`.
- **Actualizar**: un juego muestra «↑ HelixSR … disponible» cuando tu carpeta de HelixSR tiene una versión más nueva, o «↑ Hay una descarga más reciente» cuando hay una descarga de OptiScaler / FSR 4.1 más nueva (u otra versión de FSR 4.1). «↑ Actualizar todo» actualiza todos los juegos.
- **Reparar**: una actualización del juego o «Verificar la integridad de los archivos» puede devolver los archivos del juego. El juego muestra entonces qué pasó y «Reparar» vuelve a poner el escalador, guardando los archivos nuevos del juego como copia.
- **Quitar** devuelve cada archivo reemplazado o movido y quita la entrada de las opciones de lanzamiento.

### 7. Ajustes de HelixSR sin editar archivos

Con DLSS 3.7, «⚙ Ajustes» edita el `helixsr.ini` del juego con un formulario (nitidez, red int8, pase final en Ultra Rendimiento, tamaño de onda). «Predeterminado» omite la línea; las demás líneas y comentarios se conservan.

### 8. Estado en vivo y aviso superpuesto

- Los juegos de Steam en ejecución se revisan cada 3 segundos: `/proc/<pid>/maps` indica si el juego **ha cargado de verdad** HelixSR o la DLL de FSR (y OptiScaler o el cargador DLSS). No se carga nada hasta que el juego usa el escalador, así que «aún no se ha cargado» te dice qué elegir en el juego.
- Con HelixSR, el `helixsr.log` de la sesión muestra el tamaño de onda y los errores; en RDNA 3 y posteriores con el método OptiScaler se ofrece «Poner WaveSize = 64» cuando el registro indica wave32.
- El panel de detalles de un juego (el botón ⌄ de su tarjeta) tiene «Ver …log» para `helixsr.log` u `OptiScaler.log`, la carpeta del juego, el nombre de archivo de OptiScaler y, con DLSS 3.7, «⚙ Ajustes».
- Al iniciar un juego, una pequeña tarjeta abajo a la derecha muestra el resultado unos 10 segundos (o una pista tras 90 segundos). Es una ventana X11 aparte que nunca toma el foco; desactívala con el interruptor de la barra de herramientas.

### 9. Iniciar, buscar, filtrar, idiomas

- «▶ Iniciar» abre el juego con Steam. Busca por nombre (cualquier idioma) o App ID; filtros: juegos que se pueden escalar, escalador instalado, sin escalador todavía, necesitan actualización o reparación, en ejecución, todos los juegos.
- 12 idiomas de interfaz: 台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी.

### 10. Pensado para ser seguro

- No cambia nada mientras el juego se ejecuta; las descargas y la carpeta de HelixSR se comprueban antes de tocar ningún archivo.
- Cada archivo reemplazado se conserva, cada copia se verifica byte a byte, y las opciones de lanzamiento solo cambian en la entrada descrita arriba.
- El método DLSS, FSR 4.1 Lossy y los juegos con antitrampas preguntan antes. Nunca uses un escalador modificado en juegos en línea: el antitrampas puede considerarlo manipulación.

### 11. Aspecto

- Al estilo de MAKO Assistant («Liquid Glass»): una tarjeta por juego con su portada de Steam, una etiqueta de estado, lo que ofrece el juego y, mientras se ejecuta, lo que de verdad está cargado. El botón ⌄ abre los detalles (API gráfica, escaladores, carpeta del `.exe`, nombre de OptiScaler, opciones de lanzamiento) y las acciones menos frecuentes.
- Los botones son de cristal transparente: un tinte suave, un borde fino y un borde superior más claro, sin degradados. Turquesa instala, azul cambia, ámbar actualiza, rojo quita.
- Tema oscuro, claro o automático (sigue al escritorio). El registro de actividad es el cajón al pie de la ventana.

## Funciona con la instalación propia de HelixSR

Con DLSS 3.7, el Asistente de Scaler escribe el mismo registro de instalación (`helixsr-install.json`), copias de seguridad y nombres que la instalación de HelixSR, así que `helixsr-setup.sh` / `helixsr-uninstall.sh` y el Asistente de Scaler reconocen los juegos del otro. La instalación de HelixSR toma la DLL de FSR de la carpeta `ScalerAssistant` de un juego por la DLL de FSR 3.1 del juego y puede reemplazarla por HelixSR; el Asistente de Scaler marca entonces el juego como pendiente de reparación y «Reparar» quita HelixSR. Para usar DLSS 3.7 en ese juego, elígelo en el Asistente de Scaler.

## Plugin para Steam Deck (Decky Loader)

El mismo programa para el modo Juego, como plugin de [Decky Loader](https://decky.xyz) en el menú de acceso rápido.

- **Juegos**: los juegos que se pueden escalar, primero los que están en ejecución, cada uno con su etiqueta de estado y, mientras se ejecuta, lo que de verdad está cargado. Elige un juego para seleccionar DLSS 3.7 (HelixSR, cada método), FSR 4.1 Exact / Lossy o FSR 3, o para actualizarlo, repararlo, quitarlo, cambiar el nombre de archivo de OptiScaler o leer su registro. Antes llegan las mismas preguntas que en la aplicación de escritorio: descargas, el aviso de Lossy, el método DLSS y el antitrampas.
- **Configuración**: la carpeta de HelixSR (selector de archivos), las descargas y la versión de FSR 4.1 (la Steam Deck recibe la de gráficos integrados), un aviso al iniciar un juego (dice si el escalador se cargó) y el idioma (por defecto, el de Steam).
- Comparte `state.json`, las descargas y los registros de opciones de lanzamiento con la aplicación de escritorio: los juegos configurados en una aparecen en la otra. Las opciones de lanzamiento se escriben al momento a través de Steam.
- No está en el plugin: el formulario de ajustes de HelixSR (usa la aplicación de escritorio) ni el `helixsr-setup.sh` de HelixSR, que se ejecuta una vez en el modo Escritorio.

Instalación: instala Decky Loader en la Steam Deck, descarga `Scaler_Assistant-Decky-<versión>.zip` de la página [Releases](https://github.com/mosesmoon/scaler-assistant/releases) y en los ajustes de Decky → Desarrollador (activa antes el modo desarrollador en General) → «Install Plugin from ZIP File».

## Instalar el Asistente de Scaler

**AppImage (recomendado)**: incluye Python, Qt y 7-Zip.

1. Descarga `Scaler_Assistant-<versión>-x86_64.AppImage` de la página de [Releases](https://github.com/mosesmoon/scaler-assistant/releases).
2. Hazlo ejecutable: clic derecho → Propiedades → Permisos → «Permitir ejecutar el archivo como programa» (el texto varía según el gestor de archivos).
3. Haz doble clic.

```bash
chmod +x Scaler_Assistant-*-x86_64.AppImage
./Scaler_Assistant-*-x86_64.AppImage
```

Si no arranca, puede que falte FUSE; ejecútalo con `--appimage-extract-and-run`.

**Desde el código fuente**: Python 3.11+ y PyQt6 (Arch: `sudo pacman -S python-pyqt6`), y 7-Zip o bsdtar para descomprimir OptiScaler (`sudo pacman -S 7zip`).

```bash
./scaler-assistant     # ejecutar directamente
./install.sh           # instalar en ~/.local/share/scaler-assistant y añadir al menú
```

## Limitaciones conocidas

- **Solo juegos de Steam.** Los métodos FSR 4.1 / FSR 3 se han comprobado archivo por archivo con OptiScaler 0.9.4; cada juego se comporta distinto: si algo falla, consulta la lista de compatibilidad de OptiScaler o elige otro nombre de archivo para OptiScaler.
- FSR 4.1 en juegos Direct3D 11 y Vulkan pasa por la ruta Direct3D 12 de OptiScaler y está menos probado.
- HelixSR cambia rápido. El Asistente de Scaler necesita HelixSR 1.8.0 o posterior y sigue la estructura de 1.8.x / 1.9.x.
- El aviso superpuesto no aparece en el modo Juego de Steam Deck (gamescope). El plugin de Decky muestra en su lugar una notificación de Steam.
- En tailandés, vietnamita, malayo e hindi, los menús contextuales están en inglés (Qt no tiene traducciones oficiales). Steam no tiene nombres de juegos en malayo ni en hindi.

## Dónde se guardan los datos

| Ubicación | Contenido |
|---|---|
| `~/.config/scaler-assistant/state.json` | Estado del Asistente de Scaler: carpeta de HelixSR, lista de juegos, idioma, versión de FSR 4.1, nombres de OptiScaler elegidos, entradas que añadió a las opciones de lanzamiento (se toma una vez del Asistente de HelixSR) |
| `~/.local/share/scaler-assistant/components/` | Los archivos de OptiScaler y FSR 4.1 descargados |
| `~/homebrew/plugins/scaler-assistant/` | El plugin de Decky en la Steam Deck (usa el mismo estado y las mismas descargas de arriba) |
| `<juego>/…/ScalerAssistant/` | FSR 4.1 / FSR 3: DLL FidelityFX, `scaler-install.json`, `backup/` |
| `<juego>/…/HelixSR/helixsr-install.json`, junto a la DLL de FSR del juego | DLSS 3.7: registro de instalación de HelixSR (compartido con su instalación) |
| `<juego>/…/helixsr.ini`, `helixsr.log`, `OptiScaler.ini`, `OptiScaler.log` | Ajustes y registros |

## Licencias

El Asistente de Scaler es una herramienta independiente y no oficial, sin relación con el autor de HelixSR, NVIDIA, AMD, el proyecto OptiScaler o el proyecto fsr4-shader-performance-overrides, ni avalada por ellos, y no contiene ninguno de sus archivos. Cuando lo pides, descarga OptiScaler (GPL-3.0; fakenvapi MIT; DLL FidelityFX de AMD bajo la licencia de AMD) y las DLL de FSR 4.1 (GPL-2.0-or-later, DLL de AMD modificadas con el aviso de AMD) desde sus GitHub Releases. El AppImage incluye el `7zzs` de 7-Zip (GNU LGPL con la restricción de unRAR, BSD; licencia incluida). HelixSR es gratuito bajo la HelixSR Freeware License; tras su instalación, sus DLL contienen la red de NVIDIA, así que el Asistente de Scaler solo las copia entre carpetas de tu propio PC. Nunca las compartas ni las subas. El plugin de Decky incluye el mismo `7zzs`.
