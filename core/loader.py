# core/loader.py

import os
from core.logger import log, I, W, E
import importlib


async def load_extensions(bot, base_path="modules"):
    """
    Loads all extensions (cogs) inside the given folder.
    Assumes each file has an async `setup(bot)` function.
    """

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".py") and not file.startswith("_"):
                # build module path (modules.invites, etc.)
                rel_path = os.path.join(root, file)
                module = rel_path.replace("/", ".").replace("\\", ".")[:-3]

                try:
                    await bot.load_extension(module)
                    log(f"Extension Loaded {module}", I)
                except Exception as e:
                    log(f"Failed to load extension {module}: {e}", E)