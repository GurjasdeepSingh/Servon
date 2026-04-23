# core/bot.py

import os
from dataclasses import dataclass
import discord
from dotenv import load_dotenv
from discord.ext import commands
from core.logger import log, I, W, E

load_dotenv(".env")

@dataclass(slots=True)
class Config:
    TOKEN: str
    PREFIX: str = "!"
    DEBUG: bool = True


def load_config() -> Config:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN not set")

    return Config(
        TOKEN=token,
        PREFIX=os.getenv("BOT_PREFIX", "!"),
        DEBUG=os.getenv("DEBUG", "true").lower() == "true",
    )


def build_intents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True          # needed for join events
    intents.messages = True
    intents.message_content = True  # if you use prefix commands
    return intents


class Bot(commands.Bot):
    def __init__(self, config: Config):
        super().__init__(
            command_prefix=config.PREFIX,
            intents=build_intents(),
            help_command=None,
        )
        self.config = config

        # shared state (services attach here)
        self.cache = {}
        self.db = None

    async def setup_hook(self) -> None:
        # place for async startup tasks if needed
        # e.g., preload caches, schedule background tasks
        pass

    async def on_ready(self):
        # lightweight; avoid heavy work here
        log(f"Logged in as {self.user} ({self.user.id})", I)


def create_bot() -> Bot:
    config = load_config()
    return Bot(config)