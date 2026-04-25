import discord
from discord.ext import commands
from core.logger import log, E

class Control(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx:commands.Context):
        import time

        start = time.perf_counter()
        msg = await ctx.send("Pinging...")
        end = time.perf_counter()

        ws = self.bot.latency * 1000
        rtt = (end - start) * 1000

        await msg.edit(content=f"WS: {ws:.2f} ms | RTT: {rtt:.2f} ms")
    @commands.command(name="sync")
    async def sync(self, ctx:commands.Context):
        if ctx.author.id!=804407653186928652:
            return
        try:
            await self.bot.tree.sync()
            await ctx.reply("Successfully Synced App Commands!")
        except Exception as e:
            await ctx.reply(f"Error Occured while syncing commands\n-# {e}")
            log(f"Error occured while syncing commands: {e}", E)


async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(Control(bot))