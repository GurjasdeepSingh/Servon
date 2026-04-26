from discord.ui import View, Button
from discord import ui, Interaction
import discord

class PermissionHelpView(View):
    def __init__(self, channel: discord.abc.GuildChannel, missing_perms: list[str]):
        super().__init__(timeout=120)
        self.channel = channel
        self.missing_perms = missing_perms

    @ui.button(label="Help", emoji="❔", style=discord.ButtonStyle.secondary)
    async def help_button(self, itn: Interaction, button: Button):
        guild = itn.guild
        me = guild.me

        role = me.top_role if me.top_role else me
        perms_text = ", ".join(p.replace("_", " ").title() for p in self.missing_perms)

        msg = (
            f"**Missing permissions in {self.channel.mention}**\n\n"
            f"{perms_text}\n\n"
            f"### How to fix\n"
            f"1. Go to {self.channel.mention}\n"
            f"2. Click **Edit Channel** → **Permissions**\n"
            f"3. Add/select {role.mention}\n"
            f"4. Enable: **{perms_text}**\n"
            f"5. Save changes\n\n"
            f"If the channel permissions are synced with category, you may need to edit the category permissions instead."
        )

        if itn.response.is_done():
            await itn.followup.send(msg, ephemeral=True)
        else:
            await itn.response.send_message(msg, ephemeral=True)