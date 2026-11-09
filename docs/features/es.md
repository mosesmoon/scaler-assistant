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
| **FSR 4.1.2 Lite / Lite Lossy** | lo mismo | lo mismo, con la DLL de FSR 4.1 4.1.2l-exact / 4.1.2l-lossy | DLSS, FSR o XeSS |
| **FSR 4.1 (AMD)** — en lugar de Exact / Lossy en RX 9000 (RDNA 4) | lo mismo | lo mismo, con la DLL de FSR 4.1 propia de AMD | DLSS, FSR o XeSS |
| **FSR 3** | lo mismo | lo mismo; OptiScaler usa FSR 3.1.5 | DLSS, FSR o XeSS |

- **Exact** da la imagen de FSR 4.1 de AMD byte a byte, con shaders más rápidos. **Lossy** es aún más rápido y cambia ligeramente la imagen; el Asistente de Scaler muestra una vez su `WARNING.txt` antes del primer uso. Si dudas, elige Exact.
- **Lossy** es, desde las DLL de dll-2026-10-29, el antiguo Lossy2 entrenado más (el Lossy anterior desaparece): muchas menos motas oscuras en el follaje, pero sigue más despacio los aumentos de brillo. **Lite** y **Lite Lossy** usan la red más pequeña FSR 4.1.2 Lite de AMD (probablemente la que usa el controlador de AMD en gráficos integrados): Lite da la imagen de Lite byte a byte y es algo más rápido que el Lite de AMD; Lite Lossy la ejecuta en uno de cada dos fotogramas y es la versión más rápida, con una imagen cercana a Lite. Lite es algo menos preciso que FSR 4 completo en imágenes fijas y algunos movimientos, y mejor en otros. Lossy y Lite Lossy muestran cada uno su propio `WARNING.txt` una vez. Los juegos configurados con Lossy2 aparecen como desactualizados y se actualizan a Lossy.
- HelixSR solo funciona en juegos **Direct3D 12**, así que DLSS 3.7 solo se ofrece ahí. FSR 4.1 y FSR 3 también funcionan en juegos **Direct3D 11 y Vulkan**: FSR 3 de forma nativa, FSR 4.1 a través de la ruta Direct3D 12 de OptiScaler (menos probado que en juegos Direct3D 12).
- Haz clic en **«Elegir escalador»** en la fila del juego (o **«Escalador»** cuando ya hay uno): DLSS 3.7 (HelixSR) abre un submenú con sus métodos; la elección actual está marcada. Al cambiar, primero se quita la actual y todo vuelve a su sitio.

## Antes de empezar

- **FSR 4.1 y FSR 3** no necesitan nada más: la primera vez, el Asistente de Scaler pregunta si descargar OptiScaler y las DLL de FSR 4.1 para tu GPU (ver «Descargas»).
- **DLSS 3.7** necesita HelixSR, que el Asistente de Scaler no incluye. Descarga HelixSR 1.8.0 o posterior de sus [GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases), extráelo en una carpeta que conserves y ejecuta allí una vez `./helixsr-setup.sh` (crea la red de HelixSR en tu PC; cuando pregunte por los juegos puedes responder `n`). La etiqueta **HelixSR** de arriba lo explica; una carpeta de HelixSR configurada en tu carpeta personal, Descargas, Escritorio o Games se encuentra sola.
  Más fácil: pulsa **Descargar y compilar HelixSR** en esa ventana (HelixSR 2.0 o posterior); Scaler Assistant hace todo esto por ti, sin terminal.
- Los juegos se ejecutan con **Proton**. HelixSR está hecho para GPU AMD (RDNA 1 y posteriores). FSR 4.1 Exact / Lossy están hechos para Radeon RX 7000 / RX 6000 y gráficas Radeon integradas (incluida Steam Deck); otras GPU deberían ejecutarlos, pero su autor no las ha probado. FSR 4.1 no funciona en las GPU Radeon RX 5000 (RDNA 1) (todas las versiones solo muestran una imagen negra), así que el Asistente de Scaler lo muestra en gris en ellas; FSR 3 y DLSS 3.7 (HelixSR) siguen disponibles.

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

- **OptiScaler 0.9.4** (con las DLL FidelityFX de AMD: FSR 3 y el FSR 4.1 de AMD, más fakenvapi) y **FSR 4.1 Exact / Lossy / Lite / Lite Lossy** en la versión para tu GPU: tarjetas RX 7000, tarjetas RX 6000, gráfica RDNA 3 integrada en el procesador (también GeForce, Intel Arc y otras GPU), o Steam Deck y gráfica RDNA 2 integrada en el procesador. Cada versión funciona en todas; la de tu GPU es la más rápida. Si un juego se cierra con Exact, elige una versión para gráfica integrada.
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
- Los botones son cristal transparente en relieve: un tinte suave con un borde fino, un brillo curvo en la mitad superior, un destello en el borde inferior y una sombra suave debajo, todo con capas translúcidas planas, sin degradados. Los mandos de los interruptores sobresalen igual; el tema elegido es un cristal en relieve dentro de un carril hundido. Turquesa instala, azul cambia, ámbar actualiza, rojo quita.
- Tema oscuro, claro o automático (sigue al escritorio). El registro de actividad es el cajón al pie de la ventana.

## HelixSR 2.0 y la GPU

- **Descargar y compilar HelixSR en un paso**: «Descargar y compilar HelixSR» (en la ventana de HelixSR y en el plugin de Steam Deck) descarga el HelixSR más reciente (2.0 o posterior) de sus versiones en GitHub, comprobado por SHA-256, en `~/.local/share/scaler-assistant/helixsr`, y lo compila en este PC con el programa de compilación propio de HelixSR (`setup/helixsr_setup.py`, ejecutado tal cual), igual que la app de HelixSR: sin terminal y sin el paso de los juegos. Aporta lo que la compilación necesita: un Python con numpy (un Python 3.14 portátil cuando el del sistema no puede descomprimir el paquete zstd de NVIDIA, así la generación de fotogramas no requiere `zstd`) y el DirectX Shader Compiler de Microsoft, ejecutado con Proton de Steam o Wine. Los archivos de NVIDIA solo se descargan después de que aceptes en la app; el resultado se queda en tu PC. En Flatpak la compilación se ejecuta en el host. Volver a ejecutarlo solo compila lo que falta; una versión más nueva sustituye a la descargada antes.
- **HelixSR 2.0 y posteriores** guardan la DLL construida en `HelixSR-fsrfg` y ofrecen dos métodos: **HelixSR Scaler** (el OptiScaler propio de HelixSR junto al `.exe`: elige DLSS en el juego; también juegos DX11 y Vulkan) y el **método FSR** (FSR drop-in). El Asistente de Scaler instala ambos con el instalador de tu carpeta de HelixSR (`setup/helixsr_bridge.py`, el que usa la aplicación de HelixSR), así que el setup de HelixSR, su aplicación y el Asistente de Scaler reconocen, actualizan y quitan las instalaciones de los demás. El nombre de archivo lo sigue eligiendo el Asistente de Scaler, que añade la opción de lanzamiento cuando hace falta. Los juegos configurados con un método anterior pasan a HelixSR Scaler al actualizar. Las carpetas de HelixSR 1.8 / 1.9 mantienen sus tres métodos.
- **Generación de fotogramas de HelixSR** (HelixSR 2.0): en juegos DirectX 12 con DLSS Frame Generation (el `sl.dlss_g.dll` de Streamline), un juego con HelixSR Scaler muestra un interruptor «Generación de fotogramas de HelixSR» en su tarjeta (y en el plugin de Steam Deck). Usa el instalador propio de HelixSR (`scaler-fg`), que solo cambia la opción `[FrameGen]` de OptiScaler.ini; después activa DLSS Frame Generation en el juego. Necesita la generación de fotogramas que crea `./helixsr-setup.sh` (descarga los archivos DLSS Frame Generation de NVIDIA); hasta entonces el interruptor aparece en gris con el motivo. Las instalaciones nuevas la dejan desactivada; una actualización o un nuevo nombre de archivo de OptiScaler mantiene el estado. Otros juegos DX12 pueden seguir eligiendo la generación de fotogramas AMD FSR o XeSS en el menú de HelixSR Scaler (Insert); los juegos DX11 / Vulkan y la vía FSR solo tienen escalado.
- **HelixSR 3.0**: la DLL compilada es `HelixSR/helixsr.dll` (el escalador DLSS de HelixSR Scaler, «HLX DLSS»), y la vía FSR instala **HLX FSR 4**, la canalización FSR 4 propia de HelixSR, que el setup de HelixSR compila a partir del archivo de controlador FSR 4 de AMD (descarga de AMD unos 420 MB de su paquete de controladores; «Descargar y compilar HelixSR» lo pregunta antes y también trae el segundo compilador de shaders, DXC 1.9.2609). El Asistente de Scaler instala, actualiza, cambia y quita ambas vías con el instalador de la versión, igual que con 2.0; los juegos configurados con 2.0 pasan de `HelixSR-fsrfg` a `HelixSR` al actualizar. HelixSR 3.0 no tiene generación de fotogramas, así que el interruptor de arriba no aparece con él; la generación de fotogramas de AMD FSR y XeSS sigue en el menú de HelixSR Scaler. Desde HelixSR 3.2, HLX FSR 4 viene ya compilado en el ZIP (a partir del FSR SDK 2.4.0 de AMD, FSR 4.1.2): el setup ya no descarga el paquete de controladores de AMD, y el FSR propio de AMD junto a él en HelixSR Scaler es FSR 4.1.2. HelixSR 3.2.1 añade un **Preset K** opcional para HLX DLSS, que solo compila el propio setup de HelixSR (`--preset-k`; «Descargar y compilar HelixSR» no lo compila): si está compilado, entra en el juego con HelixSR Scaler (`HelixSR/k`) y sale con él, registro incluido. HelixSR 3.3 (HelixSR Scaler 2.3.0) mantiene esta estructura: HelixSR Scaler ahora también ofrece HLX FSR 4 en juegos Vulkan, y «Descargar y compilar HelixSR» también compila los núcleos Vulkan de HLX DLSS (`--vulkan` del setup), así HLX DLSS funciona de forma nativa en juegos Vulkan en lugar de pasar por el puente DirectX 12 de HelixSR Scaler. Esto duplica aproximadamente el tiempo de compilación y necesita mucha memoria; una 3.3 ya compilada sin ellos se vuelve a compilar (si fallan, la red compilada antes se sigue usando y los juegos Vulkan usan el puente). La 3.3 trae HLX FSR 4 ya compilado y sin su compilador, por lo que «Descargar y compilar HelixSR» ya no descarga DXC 1.9.2609 para él.
- **Versiones anteriores de HelixSR**: 1.8.x ofrece los tres métodos (FSR, OptiScaler, DLSS). HelixSR 1.9.0 – 1.9.3 solo traen los archivos del método FSR, así que los métodos OptiScaler y DLSS aparecen en gris («necesita HelixSR 1.8 o 2.0»); los juegos sin FSR 3.1 necesitan HelixSR 2.0 (HelixSR Scaler). Las versiones anteriores a 1.8.0 no son compatibles.
- **Método DLSS solo con una GeForce**: con una GPU AMD o Intel, los juegos no ofrecen DLSS, así que el método DLSS (HelixSR 1.x) aparece en gris con el motivo.
- **FSR 4.1.2 Lite Lossy recomendado** en gráficos integrados (Steam Deck, ROG Ally Z1 / Z2, Ryzen AI MAX) y GPU Intel: marcado «★ Recomendado» solo entre las opciones de FSR 4.1.

## Funciona con la instalación propia de HelixSR

Con DLSS 3.7, el Asistente de Scaler escribe el mismo registro de instalación (`helixsr-install.json`), copias de seguridad y nombres que la instalación de HelixSR, así que `helixsr-setup.sh` / `helixsr-uninstall.sh` y el Asistente de Scaler reconocen los juegos del otro. La instalación de HelixSR toma la DLL de FSR de la carpeta `ScalerAssistant` de un juego por la DLL de FSR 3.1 del juego y puede reemplazarla por HelixSR; el Asistente de Scaler marca entonces el juego como pendiente de reparación y «Reparar» quita HelixSR. Para usar DLSS 3.7 en ese juego, elígelo en el Asistente de Scaler.

## Plugin para Steam Deck (Decky Loader)

El mismo programa para el modo Juego, como plugin de [Decky Loader](https://decky.xyz) en el menú de acceso rápido.

- **Juegos**: los juegos que se pueden escalar, primero los que están en ejecución, cada uno con su etiqueta de estado y, mientras se ejecuta, lo que de verdad está cargado. Elige un juego para seleccionar DLSS 3.7 (HelixSR, cada método), FSR 4.1 Exact / Lossy o FSR 3, o para actualizarlo, repararlo, quitarlo, cambiar el nombre de archivo de OptiScaler o leer su registro. Antes llegan las mismas preguntas que en la aplicación de escritorio: descargas, el aviso de Lossy, el método DLSS y el antitrampas.
- **Configuración**: la carpeta de HelixSR (selector de archivos), las descargas y la versión de FSR 4.1 (la Steam Deck recibe la de gráficos integrados), un aviso al iniciar un juego (dice si el escalador se cargó) y el idioma (por defecto, el de Steam).
- Comparte `state.json`, las descargas y los registros de opciones de lanzamiento con la aplicación de escritorio: los juegos configurados en una aparecen en la otra. Las opciones de lanzamiento se escriben al momento a través de Steam.
- No está en el plugin: el formulario de ajustes de HelixSR (usa la aplicación de escritorio) ni el `helixsr-setup.sh` de HelixSR, que se ejecuta una vez en el modo Escritorio.
- En el plugin, **Descargar y compilar HelixSR** descarga y compila HelixSR 2.0 o posterior también en el modo Juego (tarda unos minutos).

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

**Instalador único (.bin)**: `Scaler_Assistant-<versión>-x86_64.bin` instala la misma aplicación empaquetada solo para tu usuario (sin root ni FUSE) en `~/.local/opt/scaler-assistant`, con el comando `scaler-assistant` y una entrada de menú. **Flatpak**: `Scaler_Assistant-<versión>-x86_64.flatpak` es un paquete de un solo archivo sobre el runtime Freedesktop 25.08 (se descarga de Flathub al instalar). Puede leer tu carpeta personal y otras unidades (tarjetas SD en `/run/media`) y ve los procesos de Steam y de los juegos con `flatpak-spawn --host`.

```bash
sh Scaler_Assistant-*-x86_64.bin                # install / instalar
sh Scaler_Assistant-*-x86_64.bin --uninstall    # remove / quitar
flatpak install --user Scaler_Assistant-*-x86_64.flatpak
flatpak run io.github.mosesmoon.ScalerAssistant
```

**Desde el código fuente**: Python 3.11+ y PyQt6 (Arch: `sudo pacman -S python-pyqt6`), y 7-Zip o bsdtar para descomprimir OptiScaler (`sudo pacman -S 7zip`).

```bash
./scaler-assistant     # ejecutar directamente
./install.sh           # instalar en ~/.local/share/scaler-assistant y añadir al menú
```

## Limitaciones conocidas

- **Solo juegos de Steam.** Los métodos FSR 4.1 / FSR 3 se han comprobado archivo por archivo con OptiScaler 0.9.4; cada juego se comporta distinto: si algo falla, consulta la lista de compatibilidad de OptiScaler o elige otro nombre de archivo para OptiScaler.
- FSR 4.1 en juegos Direct3D 11 y Vulkan pasa por la ruta Direct3D 12 de OptiScaler y está menos probado.
- HelixSR cambia rápido. El Asistente de Scaler necesita HelixSR 1.8.0 o posterior y sigue la estructura de 1.8.x / 1.9.x / 2.0.x / 3.0.x / 3.1.x / 3.2.x / 3.3.x.
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
