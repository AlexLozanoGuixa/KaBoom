import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from PantallaPrincipal import escalar_imagen_por_alto


class EscaladoIconosArcadeTests(unittest.TestCase):
    def test_conserva_proporcion_de_los_iconos_arcade(self):
        imagen = pygame.Surface((800, 477), pygame.SRCALPHA)
        escalada = escalar_imagen_por_alto(imagen, 50)
        self.assertEqual((84, 50), escalada.get_size())


if __name__ == "__main__":
    unittest.main()
