import asyncio

from .helpers import parse_player_list, parse_player_data, parse_server_details, parse_playables_update
from .models import (
    AnnouncementResponse, WipeCorpsesResponse, PlayerListResponse, PlayerDataResponse,
    PlayablesUpdateResponse, ToggleHumansResponse, Player, ServerDetailsResponse, ToggleChatResponse
)
from .exceptions import ConnectionFailed, CommandFailed


class Client:
    """
    An async RCON client for Evrima servers, allowing interaction with the server using RCON commands.

    Attributes:
        host (str): The hostname or IP address of the RCON server.
        port (int): The port number of the RCON server.
        password (str): The password for authenticating with the RCON server.
        timeout (float): The timeout duration for socket operations, default is 5.0 seconds.
    """

    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.password = password
        self.port = port
        self.timeout = 5.0

    async def _connect(self) -> None:
        """
        This method exists for API compatibility but isn't needed in async version.
        The connection is handled per-command for better reliability.
        """
        try:
            await self.get_server_details()
        except Exception as e:
            raise ConnectionFailed(f"Failed to connect to RCON server: {e}")

    async def _execute(self, command: bytes) -> str:
        """
        Executes a command on the RCON server using async sockets.

        Args:
            command (bytes): The command to execute, prefixed with the appropriate RCON command byte.
        Returns:
            str: The response from the RCON server.
        Raises:
            ConnectionFailed: If the connection to the RCON server fails.
            CommandFailed: If the command execution fails or the response is invalid.
        """
        max_retries = 3
        for attempt in range(max_retries):
            reader = None
            writer = None
            try:
                try:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(self.host, self.port),
                        timeout=self.timeout
                    )
                except asyncio.TimeoutError:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    raise ConnectionFailed(f"Connection timeout after {self.timeout}s")
                except ConnectionRefusedError:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    raise ConnectionFailed("RCON Failed: Server Offline or RCON not enabled.")
                except OSError as e:
                    if "No route to host" in str(e):
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        raise ConnectionFailed("RCON Failed: No route to host")
                    raise ConnectionFailed(f"Connection failed: {e}")

                login_payload = b'\x01' + self.password.encode('utf-8') + b'\x00'
                writer.write(login_payload)
                await asyncio.wait_for(writer.drain(), timeout=self.timeout)

                try:
                    login_response = await asyncio.wait_for(
                        reader.read(8192),
                        timeout=self.timeout
                    )
                except asyncio.TimeoutError:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    raise ConnectionFailed("Login timeout - no response from server")

                if not login_response or b"Accepted" not in login_response:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    raise ConnectionFailed("RCON login failed - invalid password or server error")

                writer.write(command)
                await asyncio.wait_for(writer.drain(), timeout=self.timeout)

                all_data = b''
                buffer_size = 8192

                while True:
                    try:
                        data = await asyncio.wait_for(
                            reader.read(buffer_size),
                            timeout=self.timeout
                        )
                        if not data:
                            break
                        all_data += data
                    except asyncio.TimeoutError:
                        break

                if not all_data:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        print("RCON command returned no data, retrying...")
                        continue
                    raise CommandFailed("No response received from RCON server")

                return all_data.decode('utf-8', errors='ignore')

            except (ConnectionFailed, CommandFailed):
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                raise CommandFailed(f"Error executing RCON command: {e}")
            finally:
                if writer:
                    try:
                        writer.close()
                        await asyncio.wait_for(writer.wait_closed(), timeout=1.0)
                    except:
                        pass
        # If all retries fail
        raise CommandFailed("Failed to execute RCON command after retries")

    async def get_server_details(self) -> ServerDetailsResponse:
        """
        Retrieves server details such as name, map, and version.

        Returns:
            ServerDetailsResponse: The response containing server details and raw response data.
        Raises:
            CommandFailed: If the command fails to execute or the response is invalid.
        """
        try:
            response = await self._execute(b'\x02\x12\x00')
            if not response.strip():
                raise CommandFailed("Empty response received for get_server_details")

            parsed_details = parse_server_details(response)
            return ServerDetailsResponse(details=parsed_details, raw=response)
        except Exception as e:
            if isinstance(e, (ConnectionFailed, CommandFailed)):
                raise
            raise CommandFailed(f"Failed to get server details: {e}")

    async def send_announcement(self, announcement: str) -> AnnouncementResponse:
        """
        Sends an announcement to the server.

        Args:
            announcement (str): The announcement message to send.
        Returns:
            AnnouncementResponse: The response containing the announcement and raw response data.
        """
        if not announcement or not announcement.strip():
            raise CommandFailed("Announcement cannot be empty")

        try:
            encoded_announcement = announcement.encode('utf-8')
            command = b'\x02\x10' + encoded_announcement + b'\x00'
            response = await self._execute(command)
            return AnnouncementResponse(announcement=announcement, raw=response)
        except Exception as e:
            if isinstance(e, (ConnectionFailed, CommandFailed)):
                raise
            raise CommandFailed(f"Failed to send announcement: {e}")

    async def wipe_corpses(self) -> WipeCorpsesResponse:
        """
        Wipes all corpses from the server.

        Returns:
            WipeCorpsesResponse: The response indicating the result of the wipe operation.
        """
        try:
            response = await self._execute(b'\x02\x13\x00')
            return WipeCorpsesResponse(raw=response)
        except Exception as e:
            if isinstance(e, (ConnectionFailed, CommandFailed)):
                raise
            raise CommandFailed(f"Failed to wipe corpses: {e}")

    async def get_players(self) -> PlayerListResponse:
        """
        Retrieves a list of players currently connected to the server.

        Returns:
            PlayerListResponse: The response containing a list of players.
        Raises:
            CommandFailed: If the command fails to execute or the response is invalid.
        """
        try:
            response = await self._execute(b'\x02\x40\x00')
            if not response.strip():
                raise CommandFailed("Empty response received for get_players")

            player_objects: List[Player] = parse_player_list(response)
            return PlayerListResponse(players=player_objects, raw=response)
        except Exception as e:
            if isinstance(e, (ConnectionFailed, CommandFailed)):
                raise
            raise CommandFailed(f"Failed to get players: {e}")

    async def get_player_data(self) -> PlayerDataResponse:
        """
        Retrieves detailed player data from the server.

        Returns:
            PlayerDataResponse: The response containing detailed player data.
        Raises:
            CommandFailed: If the command fails to execute or the response is invalid.
        """
        try:
            response = await self._execute(b'\x02\x77\x00')
            if not response.strip():
                raise CommandFailed("Empty response received for get_player_data")

            parsed_data = parse_player_data(response)
            return PlayerDataResponse(players=parsed_data, raw=response)
        except Exception as e:
            if isinstance(e, (ConnectionFailed, CommandFailed)):
                raise
            raise CommandFailed(f"Failed to get player data: {e}")

    async def update_playables(self, dinos: list[str]) -> PlayablesUpdateResponse:
        """
        Updates the playable dinosaurs on the server with the provided list of dinosaur classes.

        Args:
            dinos (List[str]): A list of dinosaur classes to be set as playable.
        Returns:
            PlayablesUpdateResponse: The response containing the status of the update operation.
        Raises:
            CommandFailed: If the command fails to execute or the response is invalid.
        """
        if not dinos:
            raise CommandFailed("Dinosaur list cannot be empty")

        try:
            dino_string = ','.join(str(dino) for dino in dinos)
            command = b'\x02\x15' + dino_string.encode('utf-8') + b'\x00'
            response = await self._execute(command)

            current_playables = parse_playables_update(response)
            return PlayablesUpdateResponse(
                raw=response,
                requested=dinos,
                current=current_playables
            )
        except Exception as e:
            if isinstance(e, (ConnectionFailed, CommandFailed)):
                raise
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
            response = await self._execute(b'\x02\x86\x00')
            # The Isle devs have the status flip-flopped, so we invert it
            status = "On" not in response
            return ToggleHumansResponse(raw=response, status=status)
        except Exception as e:
            if isinstance(e, (ConnectionFailed, CommandFailed)):
                raise
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
            response = await self._execute(b'\x02\x84\x00')
            # The Isle devs have the status flip-flopped, so we invert it
            status = "On" not in response
            return ToggleChatResponse(raw=response, status=status)
        except Exception as e:
            if isinstance(e, (ConnectionFailed, CommandFailed)):
                raise
            raise CommandFailed(f"Failed to toggle global chat: {e}")
