import os
import sys


def preparar_entorno_frozen():
    if getattr(sys, "frozen", False):
        os.chdir(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))


if __name__ == "__main__":
    preparar_entorno_frozen()
    from MainMenu import main

    main()
