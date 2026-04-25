import discord
from discord.ext import commands
from discord import app_commands
import traceback
import datetime
from core.logger import log,E


def format_permissions(perms):
    return ", ".join(p.replace("_", " ").title() for p in perms)


def cooldown_timestamp(retry_after: float):
    dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=retry_after)
    return f"<t:{int(dt.timestamp())}:R>"  # Discord relative timestamp


class ErrorHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =========================
    # PREFIX + HYBRID ERRORS
    # =========================
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):

        if hasattr(ctx.command, "on_error"):
            return  # local handler exists

        error = getattr(error, "original", error)

        # Missing permissions (user)
        if isinstance(error, commands.MissingPermissions):
            perms = format_permissions(error.missing_permissions)
            return await ctx.send(f"You are missing permissions: `{perms}`")

        # Missing permissions (bot)
        elif isinstance(error, commands.BotMissingPermissions):
            perms = format_permissions(error.missing_permissions)
            return await ctx.send(f"I am missing permissions: `{perms}`")

        # Cooldown
        elif isinstance(error, commands.CommandOnCooldown):
            ts = cooldown_timestamp(error.retry_after)
            return await ctx.send(
                f"You are on cooldown. Try again {ts}"
            )

        # Missing arguments
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"Missing argument: `{error.param.name}`")

        # Bad arguments
        elif isinstance(error, commands.BadArgument):
            return await ctx.send("Invalid argument provided.")

        # Command not found (ignore silently)
        elif isinstance(error, commands.CommandNotFound):
            return

        # Fallback (unknown error)
        else:
            command_name = ctx.command.qualified_name if ctx.command else "unknown"
            user = ctx.author
            guild = ctx.guild
            await ctx.send("An unexpected error occurred.")
            log(f"[PREFIX COMMAND] [{user.display_name}] ran [{ctx.prefix}{command_name}] in [{guild.name or "DM"}] {error}", E)
            traceback.print_exception(type(error), error, error.__traceback__)

    # =========================
    # SLASH (APP_COMMANDS)
    # =========================
    @commands.Cog.listener()
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):

        # Missing permissions (user)
        if isinstance(error, app_commands.MissingPermissions):
            perms = format_permissions(error.missing_permissions)
            return await safe_respond(interaction, 
                f"You are missing permissions: `{perms}`",
                ephemeral=True
            )

        # Missing permissions (bot)
        elif isinstance(error, app_commands.BotMissingPermissions):
            perms = format_permissions(error.missing_permissions)
            return await safe_respond(interaction, 
                f"I am missing permissions: `{perms}`",
                ephemeral=True
            )

        # Cooldown
        elif isinstance(error, app_commands.CommandOnCooldown):
            ts = cooldown_timestamp(error.retry_after)
            return await safe_respond(interaction, 
                f"You are on cooldown. Try again {ts}",
                ephemeral=True
            )

        # Check failures (generic)
        elif isinstance(error, app_commands.CheckFailure):
            return await safe_respond(interaction, 
                "You cannot use this command.",
                ephemeral=True
            )

        # Fallback
        else:
            try:
                await safe_respond(interaction, 
                    "An unexpected error occurred.",
                    ephemeral=True
                )

            except:
                pass

            command = interaction.command

            command_name = command.qualified_name if command else "unknown"
            user = interaction.user
            guild = interaction.guild

            log(f"[SLASH COMMAND] [{user.display_name}] used [/{command_name}] in [{guild.name or "DM"}] {error}", E)
            traceback.print_exception(type(error), error, error.__traceback__)

async def safe_respond(interaction: discord.Interaction, content: str, ephemeral:bool=False):
    if interaction.response.is_done():
        await interaction.followup.send(content, ephemeral=ephemeral)
    else:
        await safe_respond(interaction, content, ephemeral=ephemeral)


async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))