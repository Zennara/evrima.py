"""
evriama.rcon.client - RCON Client for The Isle: Evrima
"""
from gamercon_async import EvrimaRCON
import socket

from .helpers import parse_player_list, parse_player_data, parse_server_details, are_humans_enabled, \
    parse_playables_update
from .models import AnnouncementResponse, WipeCorpsesResponse, PlayerListResponse, PlayerDataResponse, \
    PlayablesUpdateResponse, ToggleHumansResponse, Player, ServerDetailsResponse
from .exceptions import EvrimaRCONError, ConnectionFailed, CommandFailed

class Client:
    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.password = password
        self.port = port
        self.timeout = 5

    async def _connect(self) -> EvrimaRCON:
        rcon = EvrimaRCON(self.host, self.port, self.password)
        connection = await rcon.connect()
        if connection == "Connected":
            return rcon
        else:
            raise ConnectionFailed(f"Failed to connect to RCON server: {connection}")

    async def _execute(self, command: bytes) -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                s.connect((self.host, self.port))
                login_payload = b'\x01' + self.password.encode() + b'\x00'
                s.send(login_payload)
                login_response = s.recv(8192)
                if b"Accepted" not in login_response:
                    raise ConnectionFailed("RCON login failed")
                s.send(command)
                all_data = b''
                buffer_size = 8192
                while True:
                    try:
                        s.settimeout(self.timeout)
                        data = s.recv(buffer_size)
                        if not data:
                            break
                        all_data += data
                    except socket.timeout:
                        break
                return all_data.decode('utf-8', errors='ignore')
        except ConnectionFailed:
            raise
        except Exception as e:
            if "No connection could be made because the target machine actively refused it" in str(e):
                raise ConnectionFailed("RCON Failed: Server Offline or RCON not enabled.")
            raise CommandFailed(f"Error running RCON command '{command.decode()}':\n {e}")

    async def get_server_details(self) -> ServerDetailsResponse:
        response = await self._execute(b'\x02' + b'\x12' + b'\x00')
        if not response:
            raise CommandFailed("No response received for get_server_details.")
        parsed_details = parse_server_details(response)
        return ServerDetailsResponse(details=parsed_details, raw=response)

    async def send_announcement(self, announcement: str) -> AnnouncementResponse:
        response = await self._execute(b'\x02' + b'\x10' + announcement.encode() + b'\x00')
        return AnnouncementResponse(announcement=announcement, raw=response)

    async def wipe_corpses(self) -> WipeCorpsesResponse:
        response = await self._execute(b'\x02' + b'\x13' + b'\x00')
        return WipeCorpsesResponse(raw=response)

    async def get_players(self) -> PlayerListResponse:
        response = await self._execute(b'\x02' + b'\x40' + b'\x00')
        if not response:
            raise CommandFailed("No response received for get_players.")
        player_objects: list[Player] = parse_player_list(response)

        return PlayerListResponse(players=player_objects, raw=response)

    async def get_player_data(self) -> PlayerDataResponse:
        response = await self._execute(b'\x02' + b'\x77' + b'\x00')
        if not response:
            raise CommandFailed("No response received for get_player_data.")
        parsed_data = parse_player_data(response)
        return PlayerDataResponse(players=parsed_data, raw=response)

    async def update_playables(self, dinos: list[str]) -> PlayablesUpdateResponse:
        try:
            command = b'\x02' + b'\x15' + ','.join(dinos).encode() + b'\x00'
            response = await self._execute(command)
            return PlayablesUpdateResponse(raw=response, requested=dinos, current=parse_playables_update(response))
        except Exception as e:
            raise CommandFailed(f"Failed to update playables: {e}")

    async def toggle_humans(self) -> ToggleHumansResponse:
        try:
            command = b'\x02' + b'\x86' + b'\x00'
            response = await self._execute(command)
            return ToggleHumansResponse(raw=response, status=are_humans_enabled(response))
        except Exception as e:
            raise CommandFailed(f"Failed to toggle humans: {e}")