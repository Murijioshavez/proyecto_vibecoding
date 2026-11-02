"""Punto de entrada de Astro Recolector.

    python main.py                      -> jugar
    python main.py --capturas evidencias -> generar capturas reales
    python main.py --prueba-humo 600     -> prueba de ejecución sin ventana
"""
import argparse
import os
import sys

# Permite lanzar main.py desde cualquier carpeta (doble clic, otra ruta...).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Astro Recolector")
    parser.add_argument("--capturas", metavar="CARPETA",
                        help="ejecuta una demo automática y guarda capturas")
    parser.add_argument("--sin-ventana", action="store_true",
                        help="con --capturas: no abrir ventana visible")
    parser.add_argument("--prueba-humo", type=int, metavar="FOTOGRAMAS",
                        help="prueba de ejecución sin ventana")
    args = parser.parse_args(argv)

    if args.capturas:
        from src.demo import capture_evidence
        capture_evidence(args.capturas, headless=args.sin_ventana)
    elif args.prueba_humo:
        from src.demo import smoke_test
        smoke_test(args.prueba_humo)
    else:
        from src.app import run
        run()


if __name__ == "__main__":
    main()
