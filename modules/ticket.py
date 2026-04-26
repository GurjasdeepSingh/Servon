from discord.ext import commands
import discord
from common.response import safeFollowup, safeEditMessage
from core.logger import log, E, W
from core.database import execute, get_setup_session, delete_setup_session, upsert_setup_session
from discord import app_commands
from discord.ext.commands import Cog
from discord.ui import View, Button, Select, ChannelSelect
from common.views import PermissionHelpView

steps = ["start", "choose mode", "panel channel"]




help_map = {
    0:"No help available for this step",
    1:
"""
### Channel Tickets
Each ticket is created as a separate channel under a category. This provides full control over permissions, allowing you to precisely manage who can view and respond to each ticket.

This method is more suitable for larger servers or teams that require structured support handling. However, it can quickly create many channels, which may clutter your server if not managed properly.
### Thread Tickets
Each ticket is created as a thread inside a selected channel. This keeps your server structure clean and avoids creating large numbers of channels. Threads are faster to manage and scale well for smaller or medium-sized servers.

However, threads have limited permission control compared to channels. Fine-grained access (like complex staff roles or strict visibility rules) is harder to enforce. Threads can also auto-archive if inactive unless configured otherwise.
"""
}


welcomeEmbed = discord.Embed(
    title="Welcome to ticketing with Servon!",
    description="I will guide you through steps to setup ticketing system in your server, if you do not understand meaning of the options at anypoint, you may press on the gray **❔ Help** button."
                "Lets start the setup shall we?",
    color=discord.Color.greyple()
)

class SetupGetStartedView(View):
    def __init__(self):
        super().__init__(timeout=600)
    @discord.ui.button(label="Yes!", emoji="<:checkmarkboxlineicon:1497611094942945351>", style=discord.ButtonStyle.green)
    async def yesgetstarted_button(self, itn:discord.Interaction, button:Button):
        await ticketSetup_NextStep(itn)


chooseModeEmbed = discord.Embed(
    title="First things first!",
    description="## What type of ticketing do you want?"
                "### 1. Channel Based\n### 2. Thread Based",
    color= discord.Color.fuchsia()
)

class SetupChooseModeView(View):
    def __init__(self):
        super().__init__(timeout=600)

    @discord.ui.select(options=[
            discord.SelectOption(label="Channel Based Tickets", value="channel"),
            discord.SelectOption(label="Thread Based Tickets", value="thread"),
        ],
        placeholder="Choose ticketing mode...", min_values=1, max_values=1

    )
    async def chooseModeSelect_callback(self, itn:discord.Interaction, select:Select):
        await ticketSetup_NextStep(itn, mode= select.values[0])

    @discord.ui.button(label="Help", emoji="❔", style=discord.ButtonStyle.gray)
    async def ticketsetuphelp_button(self, itn:discord.Interaction, button:Button):
        step = await getCurrentStep_safe(itn)
        if step >=0:
            await safeFollowup(itn, content=help_map[step], ephemeral=True)

choosePanelChannelEmbed = discord.Embed(
    title="Where should I send the panel!",
    description="## Which channel should contain the ticket panel?\nThe channel you select will be the place where users can go and create tickets for themselves by clicking button or selection an option.",
    color=discord.Color.green()
)

class PanelChannelSelect(ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Select a channel...",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text]
        )

    async def callback(self, itn: discord.Interaction):
        channel: discord.TextChannel = self.values[0]

        me = itn.guild.me
        perms = channel.permissions_for(me)
        missing = []

        if not perms.send_messages:
            missing.append("SEND MESSAGES")

        if not perms.embed_links:
            missing.append("EMBED LINKS")

        if missing:
            helpview = PermissionHelpView(channel, missing_perms=missing)
            return await safeFollowup(
                itn,
                content=f"I don't have required permissions in that channel.\n-# {", ".join(missing)}",
                ephemeral=True,
                view=helpview
            )

        # store + move to next step
        await ticketSetup_NextStep(
            itn,
            panel_channel=channel.id
        )
class PanelChannelSelectView(View):
    def __init__(self):
        super().__init__(timeout=600)
        self.add_item(PanelChannelSelect())

choosePanelTypeEmbed = discord.Embed(
    title="What type of panel shall it be?",
    description="## Should the panel have Buttons or a Select Menu\nClicking on button or selecting anything in selectmenu will create the ticket, so basically do you want buttons or a dropdown.",
    color=discord.Color.teal()
)

class PanelTypeView(View):
    def __init__(self):
        super().__init__(timeout=600)

    @discord.ui.select(placeholder="Select an option...", options=[discord.SelectOption(label="Button Based Panel", value="button"), discord.SelectOption(label="Dropdown Based Panel", value="select")], min_values=1, max_values=1, row=0)
    async def SelectPanelType_callback(self, itn:discord.Interaction, select:Select):
        await ticketSetup_NextStep(itn, panel_type=select.values[0])

    @discord.ui.button(label="Preview Dropdown", emoji="🪜", row=1, style=discord.ButtonStyle.gray)
    async def SelectPanelTypeHelp_callback(self, itn:discord.Interaction, button:Button):
        class ExampleDropDown(View):
            def __init__(self):
                super().__init__(timeout=120)
            @discord.ui.select(placeholder="Example Dropdown", options=[discord.SelectOption(label="Ticket Type 1", value="1"), discord.SelectOption(label="Ticket Type 2", value="2")], min_values=1, max_values=1)
            async def examplecallback(self, itn, select):
                await safeFollowup(itn, content=f"A ticket type {select.values[0]} have been created now", ephemeral=True)
        await safeFollowup(itn,embed=discord.Embed(title="Ticket Panel", description="This is an Example Panel"), view=ExampleDropDown())
    @discord.ui.button(label="Preview Button", emoji="🔘", row=1, style=discord.ButtonStyle.gray)
    async def SelectPanelTypeHelp2_callback(self, itn:discord.Interaction, button:Button):
        class ExampleButton(View):
            def __init__(self):
                super().__init__(timeout=120)
            @discord.ui.button(label="Ticket Type 1")
            async def example1callback(self, itn, button:Button):
                await safeFollowup(itn, content=f"A {button.label} would have been created now", ephemeral=True)
            @discord.ui.button(label="Ticket Type 2")
            async def example2callback(self, itn, button:Button):
                await safeFollowup(itn, content=f"A {button.label} would have been created now", ephemeral=True)
        await safeFollowup(itn, embed=discord.Embed(title="Ticket Panel", description="This is an Example Panel"), view=ExampleButton())



# ticketsetupSessions = {}

setup_map = {
    0:{
        "embed":welcomeEmbed,
        "view":SetupGetStartedView,
        "help":help_map[0]
    },
    1:{
        "embed":chooseModeEmbed,
        "view":SetupChooseModeView,
        "help":help_map[1]
    },
    2:{
        "embed":choosePanelChannelEmbed,
        "view":PanelChannelSelectView,
        "help":help_map[2]
    }
}

async def getCurrentStep_safe(itn):
    row = await get_setup_session(itn.user.id, itn.guild.id)
    # state = ticketsetupSessions.get(itn.user.id)
    if not row:
        await safeFollowup(itn, content="Setup expired. Please rerun the setup command to resume", ephemeral=True)
        return -1
    return row["step"]
    # return state["step"]

async def handle_ticket_setup(itn:discord.Interaction):
    row = await get_setup_session(itn.user.id, itn.guild.id)
    uid = itn.user.id
    if not row:
        await upsert_setup_session(uid, itn.guild.id, 0, {})
        row = {"step":0, "data":{}}
        # ticketsetupSessions[uid] = {"step":0, "data":{}}
    # state = ticketsetupSessions[uid]
    # step = state["step"]
    step = row["step"]
    kwargs = {"embed":setup_map[step]["embed"], "view":setup_map[step]["view"]()}
    if itn.response.is_done():
        await itn.edit_original_response(**kwargs)
    else:
        await itn.response.edit_message(**kwargs)


async def ticketSetup_NextStep(itn: discord.Interaction, **kwargs):
    row = await get_setup_session(itn.user.id, itn.guild.id)
    # state = ticketsetupSessions.get(itn.user.id)
    if not row:
        return await itn.response.send_message("Setup expired. Please rerun the setup command to resume", ephemeral=True)

    step = row["step"]
    # ensure data dict exists
    # data = state.setdefault("data", {})
    data = row["data"] or {}

    # merge kwargs into data
    data.update(kwargs)
    step +=1

    # advance step
    # state["step"] += 1
    await upsert_setup_session(itn.user.id, itn.guild.id, step, data)
    await handle_ticket_setup(itn)

class Ticketing(Cog):
    def __init__(self, bot:commands.Bot):
        self.bot=bot
    setupgrp = app_commands.Group(name="setup", description="Setup various modules of servon")

    @setupgrp.command(name="ticketing", description="Create your first ticketing system for the server with servon")
    async def setupTicketing(self, itn:discord.Interaction):
        await itn.response.defer()
        # ticketsetupSessions[itn.user.id] = {"step":0, "data":{}}
        await upsert_setup_session(itn.user.id, itn.guild.id, 0, {})

        await handle_ticket_setup(itn)



async def setup(bot) -> None:
    bot.add_cog(Ticketing(bot))