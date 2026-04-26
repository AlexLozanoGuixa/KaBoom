# Gestiona jugadores humanos, mandos conectados y ranuras controladas por CPU.

import pygame


class GestorJugadores:
    def __init__(self):
        self.jugadores = []  # Cada entrada guarda tipo de control, identificador e índice de skin.
        self.max_jugadores = 4

    def reset(self):
        self.jugadores.clear()

    # Gestión de ranuras controladas por CPU.
    def unir_cpu(self):
        """Añade un jugador CPU si hay hueco."""
        if len(self.jugadores) < self.max_jugadores:
            nuevo_id = f"J{len(self.jugadores) + 1}"
            self.jugadores.append({
                "tipo": "cpu",
                "id": None,
                "instance_id": f"cpu_{nuevo_id}",
                "indice": 0,
                "id_jugador": nuevo_id
            })
            return len(self.jugadores)
        return None

    def reemplazar_cpu_por_humano(self, tipo_humano, instance_id_humano, device_id=None):
        """Busca el primer hueco ocupado por una CPU y lo reemplaza por un humano."""
        for i, j in enumerate(self.jugadores):
            if j["tipo"] == "cpu":
                j["tipo"] = tipo_humano
                j["id"] = device_id
                j["instance_id"] = instance_id_humano
                j["indice"] = 0
                return True
        return False

    def unir_teclado(self):
        if not any(j["tipo"] == "teclado" for j in self.jugadores):
            # Los jugadores humanos tienen prioridad sobre las ranuras CPU.
            if self.reemplazar_cpu_por_humano("teclado", "teclado", None):
                return len(self.jugadores)

            # Si no hay CPU reemplazable, se crea una ranura humana cuando hay espacio.
            if len(self.jugadores) < self.max_jugadores:
                nuevo_id = f"J{len(self.jugadores) + 1}"
                self.jugadores.append({
                    "tipo": "teclado",
                    "id": None,
                    "instance_id": "teclado",
                    "indice": 0,
                    "id_jugador": nuevo_id
                })
                return len(self.jugadores)
        return None

    def unir_mando(self, device_index):
        joy = pygame.joystick.Joystick(device_index)
        if not joy.get_init():
            joy.init()

        instance_id = joy.get_instance_id()
        if not any(j.get("instance_id") == instance_id for j in self.jugadores):
            # Los mandos nuevos también sustituyen a una CPU si no hay huecos libres.
            if self.reemplazar_cpu_por_humano("mando", instance_id, device_index):
                return len(self.jugadores)

            # Si no hay CPU reemplazable, se crea una ranura humana cuando hay espacio.
            if len(self.jugadores) < self.max_jugadores:
                nuevo_id = f"J{len(self.jugadores) + 1}"
                self.jugadores.append({
                    "tipo": "mando",
                    "id": device_index,
                    "instance_id": instance_id,
                    "indice": 0,
                    "id_jugador": nuevo_id
                })
                return len(self.jugadores)
        return None

    def actualizar_indice(self, jugador_index, nuevo_indice):
        if 0 <= jugador_index < len(self.jugadores):
            self.jugadores[jugador_index]["indice"] = nuevo_indice

    def get_jugador_por_joy(self, instance_id):
        for j in self.jugadores:
            if j.get("instance_id") == instance_id:
                return j
        return None

    def get_teclado(self):
        for j in self.jugadores:
            if j["tipo"] == "teclado":
                return j
        return None

    def get(self, index):
        if index < len(self.jugadores):
            return self.jugadores[index]
        return None

    def todos(self):
        return self.jugadores

    def eliminar_jugador_por_joy(self, instance_id):
        self.jugadores = [j for j in self.jugadores if j.get("instance_id") != instance_id]
        self.reordenar_jugadores()

    def eliminar_teclado(self):
        self.jugadores = [j for j in self.jugadores if j["tipo"] != "teclado"]
        self.reordenar_jugadores()

    def reordenar_jugadores(self):
        # Mantiene la numeración visible J1, J2, etc. después de altas y bajas.
        for i, j in enumerate(self.jugadores):
            j["id_jugador"] = f"J{i + 1}"
gestor_jugadores = GestorJugadores()
