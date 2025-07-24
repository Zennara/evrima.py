"""
evriama.rcon.client - RCON Client for The Isle: Evrima
"""
from gamercon_async import EvrimaRCON
import socket

from .helpers import parse_player_list, parse_player_data, parse_server_details, parse_playables_update
from .models import AnnouncementResponse, WipeCorpsesResponse, PlayerListResponse, PlayerDataResponse, \
    PlayablesUpdateResponse, ToggleHumansResponse, Player, ServerDetailsResponse, ToggleChatResponse
from .exceptions import EvrimaRCONError, ConnectionFailed, CommandFailed

class Client:
    """
    Evrima RCON Client for managing server operations.

    This client allows you to connect to an Evrima RCON server and perform various operations such as
    retrieving server details, sending announcements, wiping corpses, managing players, and updating playable dinos.

    Attributes:
        host (str): The hostname or IP address of the RCON server.
        port (int): The port number of the RCON server.
        password (str): The password for authenticating with the RCON server.
        timeout (int): The timeout duration for socket operations, default is 5 seconds.
    """
    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.password = password
        self.port = port
        self.timeout = 5

    async def _connect(self) -> EvrimaRCON:
        """
        Establishes a connection to the RCON server.

        Returns:
            EvrimaRCON: An instance of the EvrimaRCON client connected to the server.
        Raises:
            ConnectionFailed: If the connection to the RCON server fails.
        """
        rcon = EvrimaRCON(self.host, self.port, self.password)
        connection = await rcon.connect()
        if connection == "Connected":
            return rcon
        else:
            raise ConnectionFailed(f"Failed to connect to RCON server: {connection}")

    async def _execute(self, command: bytes) -> str:
        """
        Executes a command on the RCON server and returns the response.

        Args:
            command (bytes): The command to execute, prefixed with the appropriate RCON command byte.
        Returns:
            str: The response from the RCON server.
        Raises:
            ConnectionFailed: If the connection to the RCON server fails.
            CommandFailed: If the command execution fails or the response is invalid.
        """
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
        """
        Retrieves server details such as name, map, and version.

        Returns:
            ServerDetailsResponse: The response containing server details and raw response data.
        Raises:
            CommandFailed: If the command fails to execute or the response is invalid.
        """
        response = await self._execute(b'\x02' + b'\x12' + b'\x00')
        if not response:
            raise CommandFailed("No response received for get_server_details.")
        parsed_details = parse_server_details(response)
        return ServerDetailsResponse(details=parsed_details, raw=response)

    async def send_announcement(self, announcement: str) -> AnnouncementResponse:
        """
        Sends an announcement to the server.

        Args:
            announcement (str): The announcement message to send.
        Returns:
            AnnouncementResponse: The response containing the announcement and raw response data.
        """
        response = await self._execute(b'\x02' + b'\x10' + announcement.encode() + b'\x00')
        return AnnouncementResponse(announcement=announcement, raw=response)

    async def wipe_corpses(self) -> WipeCorpsesResponse:
        """
        Wipes all corpses from the server.

        Returns:
            WipeCorpsesResponse: The response indicating the result of the wipe operation.
        """
        response = await self._execute(b'\x02' + b'\x13' + b'\x00')
        return WipeCorpsesResponse(raw=response)

    async def get_players(self) -> PlayerListResponse:
        """
        Retrieves a list of players currently connected to the server.

        Returns:
            PlayerListResponse: The response containing a list of players.
        Raises:
            CommandFailed: If the command fails to execute or the response is invalid.
        """
        response = await self._execute(b'\x02' + b'\x40' + b'\x00')
        if not response:
            raise CommandFailed("No response received for get_players.")
        player_objects: list[Player] = parse_player_list(response)

        return PlayerListResponse(players=player_objects, raw=response)

    async def get_player_data(self) -> PlayerDataResponse:
        """
        Retrieves detailed player data from the server.

        Returns:
            PlayerDataResponse: The response containing detailed player data.
        Raises:
            CommandFailed: If the command fails to execute or the response is invalid.
        """
        response = await self._execute(b'\x02' + b'\x77' + b'\x00')
        if not response:
            raise CommandFailed("No response received for get_player_data.")
        parsed_data = parse_player_data(response)
        return PlayerDataResponse(players=parsed_data, raw=response)

    async def update_playables(self, dinos: list[str]) -> PlayablesUpdateResponse:
        """
        Updates the playable dinosaurs on the server with the provided list of dinosaur classes.

        Args:
            dinos (list[str]): A list of dinosaur classes to be set as playable.
        Returns:
            PlayablesUpdateResponse: The response containing the status of the update operation.
        Raises:
            CommandFailed: If the command fails to execute or the response is invalid.
        """
        try:
            command = b'\x02' + b'\x15' + ','.join(dinos).encode() + b'\x00'
            response = await self._execute(command)
            return PlayablesUpdateResponse(raw=response, requested=dinos, current=parse_playables_update(response))
        except Exception as e:
            raise CommandFailed(f"Failed to update playables: {e}")

    async def toggle_humans(self) -> ToggleHumansResponse:
        """
        Toggles the availability of humans on the server.
        Warning: The Isle devs have the status flip-flopped, so we have to invert it.

        Returns:
            ToggleHumansResponse: The response containing the status of the toggle operation.
        Raises:
            CommandFailed: If the command fails to execute or the response is invalid.
        """
        try:
            command = b'\x02' + b'\x86' + b'\x00'
            response = await self._execute(command)
            # The Isle devs have the status flip-flopped, so we have to invert it
            return ToggleHumansResponse(raw=response, status="On" not in response)
        except Exception as e:
            raise CommandFailed(f"Failed to toggle humans: {e}")

    async def toggle_global_chat(self) -> ToggleChatResponse:
        """
        Toggles the global chat on the server.
        Warning: The Isle devs have the status flip-flopped, so we have to invert it.

        Returns:
            ToggleChatResponse: The response containing the status of the global chat toggle operation.
        Raises:
            CommandFailed: If the command fails to execute or the response is invalid.
        """
        try:
            command = b'\x02' + b'\x84' + b'\x00'
            response = await self._execute(command)
            # The Isle devs have the status flip-flopped, so we have to invert it
            return ToggleChatResponse(raw=response, status="On" not in response)
        except Exception as e:
            raise CommandFailed(f"Failed to toggle global chat: {e}")