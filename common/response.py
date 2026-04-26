import discord

async def safeFollowup(itn:discord.Interaction, **kwargs):
    if itn.response.is_done():
        await itn.followup.send(**kwargs)
    else:
        await itn.response.send_message(**kwargs)

async def safeEditMessage(itn: discord.Interaction, **kwargs):
    try:
        if itn.message:
            # component interaction (button/select)
            await itn.response.edit_message(**kwargs)
        else:
            # slash command / deferred
            await itn.edit_original_response(**kwargs)
    except discord.InteractionResponded:
        await itn.edit_original_response(**kwargs)
