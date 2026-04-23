import asyncio
from core.bot import create_bot
from core.logger import log
from core.loader import load_extensions

async def main():
    bot = create_bot()

    log("Bot is starting...", "I")

    # load extensions
    await load_extensions(bot)

    try:
        await bot.start(bot.config.TOKEN)
    except Exception as e:
        log(f"Fatal error: {e}", "E")
        raise


if __name__ == "__main__":
    asyncio.run(main())