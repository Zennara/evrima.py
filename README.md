# evrima.py

## Overview

`evrima.py` is a Python library that provides an async RCON client for *The Isle: Evrima* game servers. It abstracts the low-level RCON protocol into a clean, typed API, allowing developers to query server state and issue administrative commands programmatically.

## Why This Exists

Managing *The Isle: Evrima* game servers typically requires manual interaction or fragile shell scripting. This library fills the gap by offering a first-class Python interface to the Evrima RCON protocol, enabling server automation, monitoring tooling, and bot integrations to be built with minimal boilerplate.

## Tech Stack

Python 3.11+, built on `gamercon-async` for the underlying async RCON socket communication. Packaging is handled via `setuptools` with a `pyproject.toml`-based build system. Available on PyPI as `evrima.py`.

## Key Features

- Fully asynchronous client built on `asyncio`, suitable for use in bots and async server management tools
- Typed response models using Python dataclasses — player lists, detailed player state (dino species, health, stamina, hunger, thirst, location), server details, and more
- Server commands including announcements, corpse wiping, toggling humans, toggling chat, and retrieving playables updates
- Structured exception hierarchy (`ConnectionFailed`, `CommandFailed`) for predictable error handling
- Raw RCON response parsing handled internally — callers work with clean model objects rather than raw strings

## Architecture

The library is organized as a single `evrima` package with an `rcon` subpackage. The `Client` class in `client.py` owns all async command execution and delegates response parsing to `helpers.py`. Parsed data is returned as typed dataclass instances defined in `models.py`. Custom exceptions are centralized in `exceptions.py`. The public API surface is a single import: `from evrima import Client`.

## Installation / Getting Started

**Prerequisites:** Python 3.11 or higher.

**Install from PyPI:**

```bash
pip install evrima.py
```

**Basic usage:**

```python
import asyncio
from evrima import Client

async def main():
    client = Client(host="your.server.ip", port=8888, password="yourpassword")
    await client._connect()

    players = await client.get_player_list()
    for player in players.players:
        print(player.steam_id, player.name)

asyncio.run(main())
```

**Install from source:**

```bash
git clone https://github.com/zennara/evrima.py.git
cd evrima.py
pip install .
```
