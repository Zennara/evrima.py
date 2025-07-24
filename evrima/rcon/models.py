from dataclasses import dataclass, field

@dataclass
class Player:
    """
    Represents a player in the game.

    Attributes:
        steam_id (str): The unique Steam ID of the player.
        name (str): The name of the player.
    """
    steam_id: str
    name: str

@dataclass
class Location:
    """
    Represents a player's location in the game world.

    Attributes:
        X (float): The X coordinate of the player's location.
        Y (float): The Y coordinate of the player's location.
        Z (float): The Z coordinate of the player's location.
    """
    X: float
    Y: float
    Z: float

@dataclass
class PlayerData(Player):
    """
    Represents detailed data for a player in the game.

    Attributes:
        location (Location): The player's current location in the game world.
        dino (str): The type of dinosaur the player is controlling.
        growth (float): The growth stage of the dinosaur.
        health (float): The current health of the dinosaur.
        stamina (float): The current stamina of the dinosaur.
        hunger (float): The current hunger level of the dinosaur.
        thirst (float): The current thirst level of the dinosaur.
    """
    location: Location = None
    dino: str = None
    growth: float = None
    health: float = None
    stamina: float = None
    hunger: float = None
    thirst: float = None


@dataclass
class ServerDetails:
    """
    Represents the details of the game server.

    Attributes:
        name (str): The name of the server.
        password (str): The server password.
        map (str): The map currently being played on the server.
        max_players (int): The maximum number of players allowed on the server.
        current_players (int): The current number of players on the server.
        enable_mutations (bool): Whether mutations are enabled on the server.
        enable_humans (bool): Whether humans are enabled on the server.
        server_password (bool): Whether a password is required to join the server.
        queue_enabled (bool): Whether a queue system is enabled for joining the server.
        server_whitelist (bool): Whether a whitelist is enabled for the server.
        spawn_ai (bool): Whether AI spawns are enabled on the server.
        allow_recording_replay (bool): Whether recording replays is allowed on the server.
        use_region_spawning (bool): Whether region-based spawning is used on the server.
        use_region_spawn_cooldown (bool): Whether region spawn cooldowns are used on the server.
        region_spawn_cooldown_time_seconds (int): The cooldown time in seconds for region spawning.
        day_length_minutes (int): The length of a day in minutes on the server.
        night_length_minutes (int): The length of a night in minutes on the server.
        enable_global_chat (bool): Whether global chat is enabled on the server.
    """
    name: str
    password: str
    map: str
    max_players: int
    current_players: int
    enable_mutations: bool
    enable_humans: bool
    server_password: bool
    queue_enabled: bool
    server_whitelist: bool
    spawn_ai: bool
    allow_recording_replay: bool
    use_region_spawning: bool
    use_region_spawn_cooldown: bool
    region_spawn_cooldown_time_seconds: int
    day_length_minutes: int
    night_length_minutes: int
    enable_global_chat: bool


@dataclass
class BaseResponse:
    """
    Base class for all RCON responses.

    Attributes:
        success (bool): Indicates whether the command was successful.
        raw (str): The raw response string from the server.
    """
    success: bool = True
    raw: str = ""

@dataclass
class AnnouncementResponse(BaseResponse):
    """
    Represents a response to an announcement command.

    Attributes:
        announcement (str): The announcement message that was sent.
    """
    announcement: str = ""


@dataclass
class WipeCorpsesResponse(BaseResponse):
    """
    Represents a response to a command that wipes corpses from the server.
    """
    pass

@dataclass
class PlayerListResponse(BaseResponse):
    """
    Represents a response containing a list of players currently on the server.

    Attributes:
        players (list[Player]): A list of Player objects representing the players on the server.
    """
    players: list[Player] = field(default_factory=list)

@dataclass
class PlayerDataResponse(BaseResponse):
    """
    Represents a response containing detailed data for players on the server.

    Attributes:
        players (list[PlayerData]): A list of PlayerData objects representing detailed player information.
    """
    players: list[PlayerData] = field(default_factory=list)

@dataclass
class PlayablesUpdateResponse(BaseResponse):
    """
    Represents a response to a command that updates the playable dinosaurs on the server.

    Attributes:
        requested (list[str]): A list of dinosaur classes that were requested to be updated.
        current (list[str]): A list of currently available dinosaur classes after the update.
    """
    requested: list[str] = field(default_factory=list)
    current: list[str] = field(default_factory=list)

@dataclass
class ToggleHumansResponse(BaseResponse):
    """
    Represents a response to a command that toggles the availability of humans on the server.

    Attributes:
        status (bool): The new status of human availability on the server.
    """
    status: bool = None

@dataclass
class ServerDetailsResponse(BaseResponse):
    """
    Represents a response containing the details of the game server.

    Attributes:
        details (ServerDetails): An object containing the server details.
    """
    details: ServerDetails = field(default_factory=ServerDetails)


@dataclass
class ToggleChatResponse(BaseResponse):
    """
    Represents a response to a command that toggles the global chat on the server.

    Attributes:
        status (bool): The new status of global chat availability on the server.
    """
    status: bool = None
