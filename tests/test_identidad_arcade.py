import unittest
from unittest.mock import patch

from IdentidadArcade import (
    _puerto_arcade_de_ruta,
    _ruta_coincide_con_identidad,
    _ruta_sdl_a_id_instancia,
    es_joystick_control_arcade,
    normalizar_ubicacion,
)


class JoystickSimulado:
    def get_name(self):
        return "Generic USB Gamepad"


class IdentidadArcadeTests(unittest.TestCase):
    def test_normaliza_ubicacion(self):
        self.assertEqual(
            "PORT_#0010.HUB_#0001",
            normalizar_ubicacion(" Port_#0010.Hub_#0001 "),
        )

    def test_convierte_ruta_hid_en_id_pnp(self):
        ruta = (
            r"\\?\HID#VID_2341&PID_8036&MI_02#7&ABCDEF&0&0000"
            r"#{4D1E55B2-F16F-11CF-88CB-001111000030}"
        )
        self.assertEqual(
            r"HID\VID_2341&PID_8036&MI_02\7&ABCDEF&0&0000",
            _ruta_sdl_a_id_instancia(ruta),
        )

    def test_relaciona_ruta_con_prefijo_del_puerto(self):
        identidad = {
            "prefijo_padre": "6&27AA11BB&0",
            "instancia": "6&27AA11BB&0&10",
        }
        ruta = r"\\?\HID#VID_2341&PID_8036#6&27AA11BB&0&0000#{GUID}"
        self.assertTrue(_ruta_coincide_con_identidad(ruta, identidad))

    def test_clasifica_por_puerto_aunque_el_nombre_sea_generico(self):
        joystick = JoystickSimulado()
        with (
            patch("IdentidadArcade.obtener_ruta_sdl_joystick", return_value="RUTA_PANEL"),
            patch("IdentidadArcade._puerto_arcade_de_ruta", return_value=1),
        ):
            self.assertTrue(es_joystick_control_arcade(joystick))

    def test_rechaza_un_puerto_ajeno(self):
        with (
            patch("IdentidadArcade._puerto_arcade_de_ancestros", return_value=None),
            patch("IdentidadArcade._obtener_identidades_puertos", return_value=[]),
        ):
            self.assertIsNone(_puerto_arcade_de_ruta("RUTA_MANDO_NORMAL"))


if __name__ == "__main__":
    unittest.main()
