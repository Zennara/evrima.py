from evrima.rcon.models import Player


def parse_player_list(raw: str) -> list[Player]:
    raw = raw.replace("PlayerList", "").replace("\n", "").strip()
    items = [item for item in raw.split(",") if item]
    half = len(items) // 2
    steam_ids = items[:half]
    names = items[half:]
    players = [Player(steam_id=sid, name=name) for sid, name in zip(steam_ids, names)]
    return players


from evrima.rcon.models import PlayerData, Location

def parse_player_data(raw_data: str) -> list[PlayerData]:
    players = []
    for line in raw_data.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('[') and '] ' in line:
            line = line.split('] ', 1)[1]
        if 'Name:' not in line and 'PlayerDataName:' not in line:
            continue
        player = {}
        parts = line.split(', ')
        for part in parts:
            if ':' not in part:
                continue
            key, value = part.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key == 'PlayerDataName':
                key = 'Name'
            if key == 'Location':
                coords = value.split()
                try:
                    player['Location'] = {
                        'X': float(coords[0].split('=')[1]),
                        'Y': float(coords[1].split('=')[1]),
                        'Z': float(coords[2].split('=')[1])
                    }
                except (IndexError, ValueError):
                    player['Location'] = None
            elif key == 'PlayerID':
                player['PlayerID'] = value
            elif key == 'Class':
                player[key] = value.strip()[3:-2]
            else:
                player[key] = value
        # Build PlayerData object
        name = player.get('Name')
        steam_id = str(player.get('PlayerID'))
        loc = player.get('Location')
        location = Location(**loc) if loc else None
        growth = float(player.get('Growth')) if 'Growth' in player else None
        health = float(player.get('Health')) if 'Health' in player else None
        stamina = float(player.get('Stamina')) if 'Stamina' in player else None
        hunger = float(player.get('Hunger')) if 'Hunger' in player else None
        thirst = float(player.get('Thirst')) if 'Thirst' in player else None
        dino_class = player.get('Class')
        players.append(PlayerData(steam_id=steam_id, name=name, location=location,
                                  growth=growth, health=health, stamina=stamina,
                                  dino=dino_class, hunger=hunger, thirst=thirst))
    return players


from evrima.rcon.models import ServerDetails

def parse_server_details(raw: str) -> ServerDetails:
    if raw.startswith('[') and '] ' in raw:
        raw = raw.split('] ', 1)[1]
    parts = [p.strip() for p in raw.split(',')]
    data = {}
    for part in parts:
        if ':' not in part:
            continue
        key, value = part.split(':', 1)
        key = key.strip()
        value = value.strip()
        data[key] = value

    def to_bool(val):
        if val is None:
            return None
        return val.lower() == 'true'

    def to_int(val):
        try:
            return int(val)
        except (TypeError, ValueError):
            return None

    return ServerDetails(
        name=data.get('ServerDetailsServerName'),
        password=data.get('ServerPassword'),
        map=data.get('ServerMap'),
        max_players=to_int(data.get('ServerMaxPlayers')),
        current_players=to_int(data.get('ServerCurrentPlayers')),
        enable_mutations=to_bool(data.get('bEnableMutations')),
        enable_humans=to_bool(data.get('bEnableHumans')),
        server_password=to_bool(data.get('bServerPassword')),
        queue_enabled=to_bool(data.get('bQueueEnabled')),
        server_whitelist=to_bool(data.get('bServerWhitelist')),
        spawn_ai=to_bool(data.get('bSpawnAI')),
        allow_recording_replay=to_bool(data.get('bAllowRecordingReplay')),
        use_region_spawning=to_bool(data.get('bUseRegionSpawning')),
        use_region_spawn_cooldown=to_bool(data.get('bUseRegionSpawnCooldown')),
        region_spawn_cooldown_time_seconds=to_int(data.get('RegionSpawnCooldownTimeSeconds')),
        day_length_minutes=to_int(data.get('ServerDayLengthMinutes')),
        night_length_minutes=to_int(data.get('ServerNightLengthMinutes')),
        enable_global_chat=to_bool(data.get('bEnableGlobalChat')),
    )


def are_humans_enabled(raw: str) -> bool:
    if "On" in raw:
        return True
    return False


def parse_playables_update(raw: str) -> list[str]:
    raw = raw.split(':')[1].strip()
    dinos = [dino.strip() for dino in raw.split(',') if dino.strip()]
    return dinos