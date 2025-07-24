from dataclasses import dataclass, field

@dataclass
class Player:
    steam_id: str
    name: str

@dataclass
class Location:
    X: float
    Y: float
    Z: float

@dataclass
class PlayerData(Player):
    location: Location = None
    dino: str = None
    growth: float = None
    health: float = None
    stamina: float = None
    hunger: float = None
    thirst: float = None


@dataclass
class ServerDetails:
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
    success: bool = True
    raw: str = ""

@dataclass
class AnnouncementResponse(BaseResponse):
    announcement: str = ""


@dataclass
class WipeCorpsesResponse(BaseResponse):
    pass

@dataclass
class PlayerListResponse(BaseResponse):
    players: list[Player] = field(default_factory=list)

@dataclass
class PlayerDataResponse(BaseResponse):
    players: list[PlayerData] = field(default_factory=list)

@dataclass
class PlayablesUpdateResponse(BaseResponse):
    requested: list[str] = field(default_factory=list)
    current: list[str] = field(default_factory=list)

@dataclass
class ToggleHumansResponse(BaseResponse):
    status: bool = None

@dataclass
class ServerDetailsResponse(BaseResponse):
    details: ServerDetails = field(default_factory=ServerDetails)
