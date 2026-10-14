# Asistente de HelixSR — Guía de funciones

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · **Español** · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

El **Asistente de HelixSR** es una herramienta de escritorio para Linux que instala, cambia de método, actualiza y quita **[HelixSR](https://github.com/lonewolf0622/HelixSR)** en tus juegos de Steam con un clic, y muestra mientras juegas si HelixSR está funcionando de verdad.

HelixSR ejecuta la red de escalado DLSS Model E de NVIDIA en GPU AMD (RDNA 1 y posteriores) como shaders de cómputo Direct3D 12 normales, a través de Proton.

## Para quién es

HelixSR no tiene opciones de lanzamiento ni un archivo de ajustes central. Funciona colocando DLL en la carpeta de cada juego, con uno de tres métodos por juego. Hacerlo a mano implica:

1. Averiguar qué escaladores trae cada juego (FSR 3.1, DLSS, XeSS, FSR 2) y dónde está su `.exe` principal.
2. Elegir el método adecuado, renombrar los archivos del juego para conservarlos y copiar los archivos de HelixSR en los lugares correctos.
3. En el método OptiScaler, escribir las rutas correctas en `OptiScaler.ini`.
4. Repetirlo todo con cada actualización de HelixSR, y otra vez cuando una actualización del juego sobrescribe HelixSR.
5. Abrir `helixsr.log` para saber si HelixSR está funcionando de verdad.

El Asistente de HelixSR hace todo esto desde una sola ventana. La instalación propia de HelixSR pregunta juego por juego en una terminal; el Asistente los muestra en una lista para hacer clic.

## Antes de empezar

> ⚠ **El Asistente de HelixSR no incluye HelixSR y nunca lo descarga por ti.** Solo copia archivos de la carpeta de HelixSR que tú mismo preparaste.

1. **Descarga HelixSR** (1.8.0 o posterior) desde sus [versiones en GitHub](https://github.com/lonewolf0622/HelixSR/releases) y descomprímelo en una carpeta que vayas a conservar, por ejemplo tu carpeta personal.
2. **Ejecuta una vez `./helixsr-setup.sh` en esa carpeta.** Pregunta si puede descargar la DLL de DLSS de NVIDIA y con ella crea la red de HelixSR (un minuto aproximadamente). Cuando empiece a preguntar por los juegos, puedes responder `n` o cerrar la ventana: de los juegos se encarga el Asistente de HelixSR. Si encuentra la carpeta pero aún no está preparada, el Asistente ofrece el botón «Ejecutar la instalación en una terminal».
3. **Una GPU AMD RDNA 1 o posterior** (Radeon RX 5000 y posteriores, Steam Deck, APU Ryzen con gráficos RDNA). La compatibilidad con Radeon Vega es experimental en HelixSR 1.9.0.
4. **Juegos Direct3D 12 que se ejecuten con Proton** y traigan FSR 3.1, DLSS, XeSS o FSR 2.

En el primer inicio, el Asistente de HelixSR busca una carpeta de HelixSR preparada en tus carpetas personal, Descargas, Escritorio y Games. Siempre puedes elegir otra con «Elegir carpeta de HelixSR…» o haciendo clic en el indicador de HelixSR de arriba.

## Los tres métodos para meter HelixSR en un juego

Son los tres métodos del propio HelixSR (las letras son las respuestas que usa su instalación). El Asistente de HelixSR solo ofrece los que funcionan en cada juego, con el predeterminado primero.

| Método | El juego necesita | Qué cambia en la carpeta del juego | Elegir en el juego |
|---|---|---|---|
| **Método FSR** (f, predeterminado en juegos con FSR 3.1) | FSR 3.1 | El `amd_fidelityfx_upscaler_dx12.dll` (o `amd_fidelityfx_dx12.dll`) del juego se reemplaza por HelixSR; el archivo del juego se guarda como `*.original.dll` | **AMD FSR** |
| **Método OptiScaler** (o) | DLSS, XeSS o FSR 2 | OptiScaler (la versión oficial de tu carpeta de HelixSR) junto al `.exe` del juego, con su motor FSR 3.1 apuntando a una carpeta `HelixSR` al lado; todo lo que reemplaza va a `HelixSR/backup` | **DLSS** (FSR o XeSS también sirven) |
| **Método DLSS** (d, experimental) | DLSS | El cargador DLSS de HelixSR como `dxgi.dll` y HelixSR como `nvngx.dll` junto al `.exe` del juego | **DLSS** |

## Funciones

### 1. Busca tus juegos de Steam y sus escaladores

- En el primer inicio se exploran todas las bibliotecas de Steam (también las de otros discos). Tras instalar juegos, haz clic en «⟳ Volver a buscar juegos de Steam».
- En la carpeta de cada juego se buscan DLL de FSR 3.1, DLSS, XeSS y FSR 2, y la carpeta de su `.exe` principal se obtiene de la información de inicio de Steam (se tienen en cuenta lanzadores y los `*-Shipping.exe` de Unreal).
- Los juegos con **antitrampas** (Easy Anti-Cheat, BattlEye) quedan marcados.
- Los nombres de los juegos siguen el idioma de la interfaz (nombres localizados de Steam) y se ordenan según ese idioma. Los juegos que pueden usar HelixSR van primero; el filtro «Juegos que pueden usar HelixSR» está activo por defecto.

### 2. Instalación con un clic

- «Instalar HelixSR» instala con el método predeterminado; la flecha de al lado ofrece los demás. Cada método indica qué elegir en el juego.
- Antes de cambiar nada, la herramienta comprueba que la carpeta de HelixSR esté preparada (red creada) y que el juego no esté en ejecución.
- El método DLSS explica primero sus riesgos y pide confirmación. Los juegos con antitrampas también piden confirmación.
- Al terminar, el registro indica exactamente qué archivos se reemplazaron, dónde se guardaron los del juego y qué elegir en el juego.

### 3. Cambiar de método, actualizar y reparar

- **Cambiar**: «Más» → «Cambiar al …» quita primero el método actual (dejándolo todo como estaba) e instala el nuevo. Tus ajustes de HelixSR se conservan.
- **Actualizar**: cuando tu carpeta de HelixSR tiene una versión más reciente que la de un juego (nueva versión de HelixSR o red creada de nuevo), el juego muestra «↑ HelixSR … disponible» y un botón «↑ Actualizar»; «↑ Actualizar todo» actualiza todos los juegos a la vez.
- **Reparar**: una actualización del juego o «Verificar la integridad de los archivos del juego» en Steam puede volver a poner los archivos del juego encima de HelixSR. El juego explica entonces qué pasó y muestra un botón «Reparar», que vuelve a colocar HelixSR y guarda los archivos nuevos del juego como copia.
- Cuando aparece en tus Descargas (u otro lugar habitual) una carpeta de HelixSR más reciente y preparada, la herramienta ofrece una vez cambiar a ella.

### 4. Quitar

- «Quitar» elimina HelixSR y devuelve cada archivo que reemplazó o movió exactamente a como estaba.
- Los ajustes de HelixSR del juego (`helixsr.ini`) se conservan, salvo que marques «Quitar también los ajustes de HelixSR de este juego».
- Los archivos que hayas puesto tú en la carpeta `my-fsr` del juego nunca se borran.

### 5. Ajustes de HelixSR sin editar archivos

«⚙ Ajustes» edita el `helixsr.ini` del juego con un formulario. Solo se ofrecen los ajustes documentados en el README de HelixSR:

| Grupo | Ajuste | Valores |
|---|---|---|
| Nitidez | Filtro de nitidez | Predeterminado, Desactivado, NVIDIA, RCAS |
| | Intensidad | 0.00 – 1.00 |
| | Seguir el control de nitidez del juego | Predeterminado, Sí, No |
| Escalado (HelixSR 1.9.0+) | Red int8 | Predeterminado (automático), Automático, Activado, Desactivado |
| | Pase final en Ultra Rendimiento | Predeterminado (Lanczos), Lanczos, EASU (FSR 1) |
| Compatibilidad | Tamaño de onda | Predeterminado, 64, 32 |

«Predeterminado» omite la línea, así HelixSR usa su propio valor. Los comentarios y el resto de líneas del archivo se mantienen tal cual. El archivo se escribe junto a la DLL de HelixSR según el método del juego (la carpeta `HelixSR` del juego, junto a la DLL de FSR del juego o junto al `.exe`).

### 6. Estado de HelixSR en vivo (lo que realmente funciona)

Los juegos de Steam en ejecución se revisan cada 3 segundos:

- Proton carga las DLL de Windows desde sus archivos, así que la herramienta ve en `/proc/<pid>/maps` si el juego **ha cargado de verdad HelixSR** (y OptiScaler o el cargador DLSS).
- HelixSR solo se carga cuando el juego usa el escalador. Por eso «HelixSR aún no está cargado» te dice qué elegir en los ajustes gráficos del juego.
- Se lee el `helixsr.log` de la sesión actual: se muestran el tamaño de onda de los núcleos de la red y las líneas de error. «Más» → «Ver helixsr.log» muestra el registro completo con un botón para copiar.
- En GPU **RDNA 3 y posteriores**, en juegos con el método OptiScaler, el README de HelixSR recomienda `WaveSize = 64` cuando el registro indica wave32. La herramienta lo detecta y ofrece «Establecer WaveSize = 64» con un clic.
- El indicador de GPU de arriba muestra la generación de tu GPU (por ejemplo «AMD RDNA 3 (gfx1100)»).

### 7. Aviso al iniciar un juego

Si el Asistente de HelixSR está abierto cuando arranca un juego con HelixSR, en cuanto HelixSR se carga aparece abajo a la derecha, durante unos 10 segundos, una pequeña tarjeta con la versión, el método y el tamaño de onda (una vez por inicio; los juegos que ya estaban abiertos antes que la herramienta se omiten). Si HelixSR sigue sin cargarse a los 90 segundos, la tarjeta indica qué elegir en el juego. El aviso es una ventana X11 (XWayland) aparte que nunca toma el foco y deja pasar los clics. Se desactiva con la casilla de la barra de herramientas. No aparece en el modo Juego de Steam Deck (gamescope).

### 8. Iniciar juegos, buscar y filtrar

- Cada fila tiene un botón «▶ Iniciar» (a través de `steam://rungameid/<AppID>`); muestra «En ejecución» mientras el juego está abierto.
- Busca por nombre del juego (en cualquier idioma) o App ID. Filtros: juegos que pueden usar HelixSR, instalado, no instalado, necesitan actualización o reparación, en ejecución, todos los juegos.

### 9. Doce idiomas de interfaz

台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी. En el primer inicio se usa el idioma del sistema; cámbialo arriba a la derecha (se aplica al momento y se recuerda).

### 10. Pensado para ser seguro

- No se cambia nada si la carpeta de HelixSR no está preparada o si el juego está en ejecución.
- Cada archivo que HelixSR reemplaza se conserva (`*.original.dll` o `HelixSR/backup`), y cada archivo copiado se comprueba byte a byte.
- Un `OptiScaler.ini` que ya tuvieras se respalda y se restaura al quitar; una DLL de FSR que hayas reemplazado a mano en la carpeta `HelixSR` del juego se conserva al actualizar.
- El método DLSS y los juegos con antitrampas requieren una confirmación explícita.

## Funciona junto a la instalación propia de HelixSR

El Asistente de HelixSR escribe el mismo registro de instalación (`helixsr-install.json`), las mismas copias y los mismos nombres de archivo que la instalación de HelixSR. Por eso:

- Los juegos preparados con `helixsr-setup.sh` aparecen como instalados en el Asistente de HelixSR, con su método, y se pueden cambiar, actualizar o quitar desde ahí.
- Los juegos preparados con el Asistente de HelixSR los reconocen la instalación de HelixSR y `helixsr-uninstall.sh`, que pueden actualizarlos o quitarlos.

## Instalar el Asistente de HelixSR

**AppImage (recomendado)**: incluye Python y Qt, no hace falta instalar nada más.

1. Descarga `HelixSR_Assistant-<versión>-x86_64.AppImage` desde la página de [Releases](https://github.com/mosesmoon/helixsr-assistant/releases).
2. Hazlo ejecutable: clic derecho en el archivo → Propiedades → Permisos, y activa «Permitir ejecutar el archivo como un programa» (el texto varía según el gestor de archivos).
3. Haz doble clic para abrir el Asistente de HelixSR.

O en una terminal:

```bash
chmod +x HelixSR_Assistant-*-x86_64.AppImage
./HelixSR_Assistant-*-x86_64.AppImage
```

Si no arranca, puede que a tu sistema le falte FUSE; ejecútalo entonces con `./HelixSR_Assistant-*-x86_64.AppImage --appimage-extract-and-run`.

**Desde el código fuente**: requiere Python 3.11 o posterior y PyQt6 (Arch: `sudo pacman -S python-pyqt6`).

```bash
./helixsr-assistant    # ejecutar directamente
./install.sh           # instalar en ~/.local/share/helixsr-assistant y añadir una entrada al menú
```

## Limitaciones conocidas

- **Solo juegos de Steam.** Para juegos de otras tiendas, usa la instalación propia de HelixSR (arrastra la carpeta del juego).
- HelixSR solo funciona en juegos Direct3D 12. Un juego listado con una DLL de DLSS o FSR puede usar igualmente Vulkan o Direct3D 11; en ese caso HelixSR no hace nada.
- HelixSR cambia muy rápido. El Asistente de HelixSR necesita HelixSR 1.8.0 o posterior y está hecho para la estructura de las versiones 1.8.x y 1.9.x; si una versión futura de HelixSR cambia cómo se preparan los juegos, usa la instalación propia de HelixSR hasta que se actualice el Asistente.
- El aviso no aparece en el modo Juego de Steam Deck (gamescope), y los juegos en pantalla completa exclusiva de Wayland nativo pueden taparlo.
- En tailandés, vietnamita, malayo e hindi, los menús contextuales están en inglés (Qt no tiene traducciones oficiales para estos idiomas). Steam no tiene nombres de juegos en malayo ni en hindi, así que esos dos idiomas muestran siempre los nombres originales.

## Dónde se guardan los datos

| Ubicación | Contenido |
|---|---|
| `~/.config/helixsr-assistant/state.json` | Estado propio del Asistente de HelixSR: carpeta de HelixSR, caché de la lista de juegos, idioma de la interfaz, ajuste del aviso |
| `<juego>/…/HelixSR/helixsr-install.json`, junto a la DLL de FSR del juego | Registro de instalación de HelixSR (compartido con su instalación) |
| `<juego>/…/helixsr.ini` | Ajustes de HelixSR para ese juego |
| `<juego>/…/helixsr.log` | Lo que informó HelixSR la última vez que se ejecutó el juego |

## Licencias

El Asistente de HelixSR es una herramienta independiente y no oficial. No está afiliada ni respaldada por el autor de HelixSR, NVIDIA, AMD ni el proyecto OptiScaler, y no contiene ninguno de sus archivos. HelixSR es gratuito bajo la HelixSR Freeware License. Una vez ejecutada su instalación, las DLL de HelixSR contienen la red de NVIDIA: el Asistente de HelixSR solo las copia entre carpetas de tu propio PC. No las compartas ni las subas nunca.
