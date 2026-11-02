# Registro de iteraciones — Astro Recolector

Este registro resume cada iteración real del desarrollo, en orden cronológico.
Las diferencias exactas de código están en `docs/diffs/` (generadas con `diff -ruN`
entre copias del código guardadas al terminar cada iteración).

| # | Tipo | Detonante (evidencia) | Archivos | Diff |
|---|------|-----------------------|----------|------|
| 0 | Versión base (v1) | — | `main.py`, `src/settings.py`, `src/entities.py`, `src/game.py`, `src/render.py`, `src/app.py` | — |
| 1 | Mejora visual | Revisión del aspecto de la v1: fondo plano y figuras sin animación | `src/render.py`, `src/effects.py` (nuevo) | `diffs/iteracion1_visual.diff` |
| 2 | Mejora de jugabilidad | `docs/diagnostico_v1.txt`, punto 1: un solo meteoro quitaba las 3 vidas en 0,5 s | `src/game.py`, `src/entities.py`, `src/settings.py`, `src/render.py` | `diffs/iteracion2_jugabilidad.diff` |
| 3 | Estabilidad / calidad | `docs/diagnostico_v1.txt`, puntos 2, 3 y 4 | `src/game.py`, `src/settings.py`, `src/demo.py` (nuevo), `main.py`, `tests/` | `diffs/iteracion3_estabilidad.diff` |
| 4 | Corrección tras ejecutar en Windows | `docs/registro_windows/intento1_*.txt` y `docs/registro_windows/antes_fix_halo_*.png` | `requirements.txt`, `src/render.py`, `ejecutar_pruebas_y_capturas.bat` | `diffs/iteracion4_correccion_halo.diff` |

---

## Diagnóstico de la versión base

El script `docs/diagnostico.py` se ejecutó sobre la v1 y se guardó la salida en
`docs/diagnostico_v1.txt`:

```
1) vidas tras 0.5 s de contacto con UN meteoro: 0 estado: game_over
2) meteoros en memoria tras 120 s: 109 visibles: 5
3) récord corrupto -> excepción: JSONDecodeError
4) dt=3s: desplazamiento de la nave en un solo frame: 462 px
```

El mismo script ejecutado sobre la versión final (`docs/diagnostico_final.txt`):

```
1) vidas tras 0.5 s de contacto con UN meteoro: 2 estado: playing
2) meteoros en memoria tras 120 s: 5 visibles: 5
3) récord corrupto: OK
4) dt=3s: desplazamiento de la nave en un solo frame: 16 px
```

---

## Iteración 1 — Mejora visual

- **Estado anterior:** fondo de un solo color (`screen.fill`), nave, estrellas y meteoros como polígonos planos, HUD con tres textos sueltos ("Puntos", "Nivel", "Vidas"), sin animaciones ni respuesta visual al recoger o chocar.
- **Limitación detectada:** el juego funcionaba, pero no comunicaba lo que pasaba: recoger una estrella o recibir un golpe no tenía ningún efecto en pantalla, y la sensación de velocidad no cambiaba al subir de nivel.
- **Instrucción utilizada:** "Mejora la calidad visual sin usar imágenes externas: fondo con profundidad, halos, partículas al recoger y al chocar, textos flotantes de puntos, sacudida de pantalla y un HUD más legible. Mantén los efectos fuera de la lógica del juego."
- **Modificación realizada:**
  - Nuevo módulo `src/effects.py` (sin Pygame): `Particle`, `FloatingText`, `Starfield` (3 capas con paralaje) y `Effects`, que reacciona a los eventos `collect`, `hit` y `level_up` emitidos por `Game`.
  - `src/render.py`: degradado de fondo, estrellas parpadeantes, halos, llama animada de la nave, estela y cráter en meteoros, panel HUD con corazones y barra de progreso de nivel, menú con título flotante y botones, superposición semitransparente en pausa y fin de partida.
  - La velocidad del fondo aumenta con el nivel (`boost`).
- **Estado posterior:** cada acción tiene respuesta visual. Ver `evidencias/03_partida_en_ejecucion.png` y `evidencias/05_mejora_escudo_y_efectos.png`.

## Iteración 2 — Mejora de jugabilidad

- **Estado anterior:** al tocar un meteoro se restaba una vida **en cada fotograma** mientras durase el contacto; el meteoro no desaparecía. Puntuación fija de 10 por estrella.
- **Limitación detectada:** el diagnóstico mostró `vidas: 0, estado: game_over` tras 0,5 s de contacto con un único meteoro. Además, la puntuación no premiaba la habilidad. La pantalla final mostraba "¡NUEVO RÉCORD!" con una comparación (`score >= highscore`) que también era cierta al empatar.
- **Instrucción utilizada:** "Corrige el daño repetido con invulnerabilidad temporal y destruye el meteoro al chocar. Añade profundidad sin complicar los controles: un combo multiplicador por encadenar estrellas y un escudo que absorba un golpe. Emite un evento al subir de nivel."
- **Modificación realizada:**
  - `src/game.py`: métodos `collect_star()` (combo ×1…×5 con ventana de 1,6 s) y `hit_by()` (invulnerabilidad 1,5 s, el escudo absorbe el golpe, el combo se reinicia); generación periódica de `PowerUp`; evento `level_up`; bandera `new_record`.
  - `src/entities.py`: clase `PowerUp`.
  - `src/settings.py`: constantes `INVULNERABLE_TIME`, `COMBO_WINDOW`, `COMBO_MAX`, `SHIELD_*`.
  - `src/render.py`: parpadeo durante la invulnerabilidad, anillo del escudo, indicadores "COMBO xN" y "ESCUDO".
- **Estado posterior:** un choque cuesta exactamente una vida (prueba `test_invulnerabilidad_evita_daño_repetido`). Ver `evidencias/04_puntuacion_y_combo.png`.

## Iteración 3 — Estabilidad y calidad del código

- **Estado anterior:** los meteoros nunca se eliminaban de la lista; un `dt` grande movía la nave cientos de píxeles en un fotograma; un `highscore.json` corrupto bloqueaba el arranque; el récord se guardaba en el directorio de trabajo actual (diferente según cómo se lance el juego en Windows).
- **Limitación detectada:** diagnóstico puntos 2, 3 y 4 (109 meteoros en memoria con solo 5 visibles; `JSONDecodeError`; 462 px en un fotograma).
- **Instrucción utilizada:** "Haz el juego robusto: elimina objetos fuera de pantalla, limita dt, pon un tope de objetos, haz que la lectura/escritura del récord nunca rompa el juego y que use una ruta relativa al proyecto. Añade un modo de prueba de humo y un modo de capturas que ejecuten el juego real, y pruebas automatizadas."
- **Modificación realizada:**
  - `src/game.py`: `on_screen()` y filtrado de listas, `MAX_METEORS`, `dt = max(0.0, min(dt, cfg.MAX_DT))`, `load_highscore()`/`save_highscore()` con `try/except` y validación del valor.
  - `src/settings.py`: `PROJECT_DIR = Path(__file__).resolve().parent.parent`.
  - `main.py`: `argparse` con `--prueba-humo` y `--capturas`; `sys.path` relativo al propio archivo.
  - `src/demo.py`: piloto automático y generador de capturas con `pygame.image.save`.
  - A continuación (fase de pruebas) se escribieron las 58 pruebas de `tests/`, incluidas pruebas de regresión para cada punto del diagnóstico.
- **Estado posterior:** ver `docs/diagnostico_final.txt` (5 meteoros en memoria, récord corrupto tolerado, 16 px máx. por fotograma).

## Iteración 4 — Correcciones detectadas al ejecutar en Windows

Primera ejecución real en Windows 11 (Python 3.14.7) con `ejecutar_pruebas_y_capturas.bat`:

1. **Error de instalación.** `pip install pygame` intentó compilar `pygame-2.6.1.tar.gz` y falló (`ModuleNotFoundError: No module named 'setuptools._distutils.msvccompiler'`): Pygame clásico no publica binarios para Python 3.14. Como `pip` abortó, tampoco se instaló `pytest` (`No module named pytest`). Registro: `docs/registro_windows/intento1_log_windows.txt`.
   **Corrección:** `requirements.txt` usa `pygame-ce` (fork mantenido por la comunidad, misma API `import pygame`, con binarios para 3.14). Segunda ejecución: `Successfully installed ... pygame-ce-2.5.8 ... pytest-9.2.0`.
2. **Defecto visual.** Las capturas reales mostraron los halos como discos sólidos (gran círculo violeta en el menú, círculos opacos alrededor de estrellas y meteoros): `docs/registro_windows/antes_fix_halo_*.png`. Causa: `BLEND_RGBA_ADD` suma los canales RGB ignorando el alfa.
   **Corrección:** el halo se dibuja en una superficie opaca con el color ya multiplicado por su intensidad y se mezcla con `BLEND_RGB_ADD` (`src/render.py`, método `glow`). Comparación: `evidencias/09_comparacion_mejora_visual_halo.png`.
3. **Codificación de consola.** El log mostraba `lM-mmite` en lugar de `límite` (consola cp1252). **Corrección:** `set PYTHONIOENCODING=utf-8` en el `.bat`.

Tras las correcciones: `58 passed` en Windows (`evidencias/resultado_pruebas_windows.txt`).
