import ctypes
import re
import sys
import time
import unicodedata
from ctypes import wintypes
from pathlib import Path

try:
    import winreg
except ImportError:
    winreg = None


PUERTOS_CONTROL_ARCADE = {
    "PORT_#0010.HUB_#0001": 1,
    "PORT_#0009.HUB_#0001": 2,
}
NOMBRES_ARCADE_PREDEFINIDOS = {
    "controlador jugador 1",
    "controlador jugador 2",
}

CR_SUCCESS = 0
MAX_DEVICE_ID_LEN = 512
INTERVALO_CACHE_REGISTRO = 2.0

_cfgmgr32 = None
_sdl2 = None
_cache_identidades = []
_instante_cache_identidades = 0.0
_rutas_arcade_confirmadas = {}


def normalizar_nombre_dispositivo(nombre):
    """Normaliza nombres de SDL para compararlos sin depender de tildes o símbolos."""
    texto = unicodedata.normalize("NFKD", str(nombre or ""))
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return re.sub(r"[^a-z0-9]+", " ", texto.casefold()).strip()


def normalizar_ubicacion(ubicacion):
    """Unifica el formato con el que Windows representa un puerto físico USB."""
    return str(ubicacion or "").strip().upper()


def es_nombre_control_arcade(nombre):
    """Mantiene compatibilidad con paneles cuyo descriptor USB ya sea correcto."""
    nombre_normalizado = normalizar_nombre_dispositivo(nombre)
    return any(
        re.search(rf"(?:^|\s){re.escape(nombre_arcade)}(?:\s|$)", nombre_normalizado)
        for nombre_arcade in NOMBRES_ARCADE_PREDEFINIDOS
    )


def _leer_valor_registro(clave, nombre, predeterminado=""):
    try:
        valor, _ = winreg.QueryValueEx(clave, nombre)
    except OSError:
        return predeterminado
    if isinstance(valor, (list, tuple)):
        return " ".join(str(elemento) for elemento in valor)
    return str(valor)


def _enumerar_identidades_puertos():
    """Localiza en el registro los dispositivos conectados a los dos puertos arcade."""
    if winreg is None or sys.platform != "win32":
        return []

    identidades = []
    ruta_enum = r"SYSTEM\CurrentControlSet\Enum\USB"
    try:
        raiz = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ruta_enum)
    except OSError:
        return identidades

    with raiz:
        indice_dispositivo = 0
        while True:
            try:
                nombre_dispositivo = winreg.EnumKey(raiz, indice_dispositivo)
            except OSError:
                break
            indice_dispositivo += 1
            if "VID_" not in nombre_dispositivo.upper() or "PID_" not in nombre_dispositivo.upper():
                continue

            try:
                clave_dispositivo = winreg.OpenKey(raiz, nombre_dispositivo)
            except OSError:
                continue

            with clave_dispositivo:
                indice_instancia = 0
                while True:
                    try:
                        nombre_instancia = winreg.EnumKey(clave_dispositivo, indice_instancia)
                    except OSError:
                        break
                    indice_instancia += 1
                    try:
                        clave_instancia = winreg.OpenKey(clave_dispositivo, nombre_instancia)
                    except OSError:
                        continue

                    with clave_instancia:
                        ubicacion = normalizar_ubicacion(
                            _leer_valor_registro(clave_instancia, "LocationInformation")
                        )
                        if ubicacion not in PUERTOS_CONTROL_ARCADE:
                            continue
                        identidades.append(
                            {
                                "jugador": PUERTOS_CONTROL_ARCADE[ubicacion],
                                "ubicacion": ubicacion,
                                "vid_pid": nombre_dispositivo.upper(),
                                "instancia": nombre_instancia.upper(),
                                "prefijo_padre": _leer_valor_registro(
                                    clave_instancia,
                                    "ParentIdPrefix",
                                ).upper(),
                            }
                        )
    return identidades


def _obtener_identidades_puertos():
    global _cache_identidades, _instante_cache_identidades

    ahora = time.monotonic()
    if ahora - _instante_cache_identidades >= INTERVALO_CACHE_REGISTRO:
        _cache_identidades = _enumerar_identidades_puertos()
        _instante_cache_identidades = ahora
    return _cache_identidades


def _cargar_cfgmgr32():
    global _cfgmgr32
    if _cfgmgr32 is False:
        return None
    if _cfgmgr32 is not None:
        return _cfgmgr32
    if sys.platform != "win32":
        _cfgmgr32 = False
        return None

    try:
        biblioteca = ctypes.WinDLL("cfgmgr32.dll")
        biblioteca.CM_Locate_DevNodeW.argtypes = [
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPCWSTR,
            wintypes.ULONG,
        ]
        biblioteca.CM_Locate_DevNodeW.restype = wintypes.ULONG
        biblioteca.CM_Get_Parent.argtypes = [
            ctypes.POINTER(wintypes.DWORD),
            wintypes.DWORD,
            wintypes.ULONG,
        ]
        biblioteca.CM_Get_Parent.restype = wintypes.ULONG
        biblioteca.CM_Get_Device_IDW.argtypes = [
            wintypes.DWORD,
            wintypes.LPWSTR,
            wintypes.ULONG,
            wintypes.ULONG,
        ]
        biblioteca.CM_Get_Device_IDW.restype = wintypes.ULONG
    except (OSError, AttributeError):
        _cfgmgr32 = False
        return None

    _cfgmgr32 = biblioteca
    return _cfgmgr32


def _ruta_sdl_a_id_instancia(ruta_sdl):
    """Convierte una ruta de interfaz SDL en un identificador PnP de Windows."""
    ruta = str(ruta_sdl or "").strip()
    for prefijo in ("\\\\?\\", "\\??\\"):
        if ruta.startswith(prefijo):
            ruta = ruta[len(prefijo):]
            break
    partes = ruta.split("#")
    if len(partes) < 3 or partes[0].upper() not in {"HID", "USB"}:
        return ""
    return "\\".join(partes[:3])


def _id_dispositivo_desde_devinst(biblioteca, devinst):
    buffer = ctypes.create_unicode_buffer(MAX_DEVICE_ID_LEN)
    resultado = biblioteca.CM_Get_Device_IDW(
        devinst,
        buffer,
        len(buffer),
        0,
    )
    return buffer.value if resultado == CR_SUCCESS else ""


def _ubicacion_id_dispositivo(id_dispositivo):
    if winreg is None or not id_dispositivo:
        return ""
    ruta = rf"SYSTEM\CurrentControlSet\Enum\{id_dispositivo}"
    try:
        clave = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ruta)
    except OSError:
        return ""
    with clave:
        return normalizar_ubicacion(_leer_valor_registro(clave, "LocationInformation"))


def _puerto_arcade_de_ancestros(ruta_sdl):
    """Recorre la jerarquía PnP hasta encontrar la ubicación del puerto USB físico."""
    biblioteca = _cargar_cfgmgr32()
    id_instancia = _ruta_sdl_a_id_instancia(ruta_sdl)
    if biblioteca is None or not id_instancia:
        return None

    devinst = wintypes.DWORD()
    if biblioteca.CM_Locate_DevNodeW(ctypes.byref(devinst), id_instancia, 0) != CR_SUCCESS:
        return None

    visitados = set()
    for _ in range(12):
        id_dispositivo = _id_dispositivo_desde_devinst(biblioteca, devinst.value)
        if not id_dispositivo or id_dispositivo in visitados:
            break
        visitados.add(id_dispositivo)

        ubicacion = _ubicacion_id_dispositivo(id_dispositivo)
        if ubicacion in PUERTOS_CONTROL_ARCADE:
            return PUERTOS_CONTROL_ARCADE[ubicacion]

        padre = wintypes.DWORD()
        if biblioteca.CM_Get_Parent(ctypes.byref(padre), devinst.value, 0) != CR_SUCCESS:
            break
        devinst = padre
    return None


def _ruta_coincide_con_identidad(ruta_sdl, identidad):
    """Respalda la detección PnP comparando identificadores estables de la ruta HID."""
    ruta = str(ruta_sdl or "").upper().replace("#", "\\")
    prefijo_padre = identidad.get("prefijo_padre", "")
    instancia = identidad.get("instancia", "")
    if prefijo_padre and prefijo_padre in ruta:
        return True
    if instancia and instancia in ruta:
        return True
    return False


def _puerto_arcade_de_ruta(ruta_sdl):
    ruta_normalizada = str(ruta_sdl or "").strip().upper()
    if not ruta_normalizada:
        return None
    if ruta_normalizada in _rutas_arcade_confirmadas:
        return _rutas_arcade_confirmadas[ruta_normalizada]

    jugador = _puerto_arcade_de_ancestros(ruta_sdl)
    if jugador is not None:
        _rutas_arcade_confirmadas[ruta_normalizada] = jugador
        return jugador

    for identidad in _obtener_identidades_puertos():
        if _ruta_coincide_con_identidad(ruta_sdl, identidad):
            _rutas_arcade_confirmadas[ruta_normalizada] = identidad["jugador"]
            return identidad["jugador"]
    return None


def _cargar_sdl2():
    global _sdl2
    if _sdl2 is False:
        return None
    if _sdl2 is not None:
        return _sdl2

    try:
        import pygame
    except ImportError:
        _sdl2 = False
        return None

    bibliotecas = []
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.WinDLL("kernel32.dll")
            kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
            kernel32.GetModuleHandleW.restype = wintypes.HMODULE
            handle = kernel32.GetModuleHandleW("SDL2.dll")
            if handle:
                bibliotecas.append(ctypes.CDLL("SDL2.dll", handle=handle))
        except OSError:
            pass

    candidatos = []
    carpeta_temporal = getattr(sys, "_MEIPASS", None)
    if carpeta_temporal:
        candidatos.append(Path(carpeta_temporal) / "SDL2.dll")
    candidatos.append(Path(pygame.__file__).resolve().with_name("SDL2.dll"))

    for ruta in candidatos:
        try:
            bibliotecas.append(ctypes.CDLL(str(ruta)))
        except OSError:
            continue

    for biblioteca in bibliotecas:
        try:
            biblioteca.SDL_JoystickPathForIndex.argtypes = [ctypes.c_int]
            biblioteca.SDL_JoystickPathForIndex.restype = ctypes.c_char_p
        except AttributeError:
            continue
        _sdl2 = biblioteca
        return _sdl2

    _sdl2 = False
    return None


def _indice_sdl_del_joystick(joystick):
    try:
        import pygame
        instance_id = joystick.get_instance_id()
    except (ImportError, AttributeError, RuntimeError):
        return None

    for indice in range(pygame.joystick.get_count()):
        try:
            candidato = pygame.joystick.Joystick(indice)
            if not candidato.get_init():
                candidato.init()
            if candidato.get_instance_id() == instance_id:
                return indice
        except pygame.error:
            continue
    return None


def obtener_ruta_sdl_joystick(joystick):
    """Obtiene la ruta HID/USB que SDL asocia al joystick recibido."""
    biblioteca = _cargar_sdl2()
    indice = _indice_sdl_del_joystick(joystick)
    if biblioteca is None or indice is None:
        return ""
    try:
        ruta = biblioteca.SDL_JoystickPathForIndex(indice)
    except (OSError, AttributeError):
        return ""
    return ruta.decode("utf-8", errors="replace") if ruta else ""


def es_joystick_control_arcade(joystick):
    """Clasifica el control por su puerto físico y usa el nombre solo como respaldo."""
    ruta_sdl = obtener_ruta_sdl_joystick(joystick)
    if _puerto_arcade_de_ruta(ruta_sdl) is not None:
        return True
    try:
        return es_nombre_control_arcade(joystick.get_name())
    except (AttributeError, RuntimeError):
        return False
