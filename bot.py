import math
import traceback

from credentials import vk_fcbot_token, vk_fcbot_beta_token, vk_personal_audio_token
from fuzzywuzzy import fuzz
from vk_botting import CommandNotFound, MissingRequiredArgument, CommandOnCooldown

from cogs.moderation import *
from cogs.profiles import *

FCMember._bot = fcbot


async def other_setups():
    await fcbot.refresh_albums()
    if not dev:
        for comm in fcbot.walk_commands():
            if comm.used_art and comm.used_art not in fcbot.album_converter:
                oid, aid = await fcbot.create_album(comm.name.capitalize(), f'Арты для команды "{comm.name.capitalize()}"')
                await fcbot.add_album(comm.used_art, oid, aid)


@fcbot.listen()
async def on_ready():
    await fcbot.attach_user_token(vk_personal_audio_token)
    moderation_setup()
    profiles_setup()
    await other_setups()
    await inject_callbacks()
    await fcbot.send_update_message()
    print(f'Logged in as {fcbot.group.name}')


@fcbot.check
async def roles_check(ctx):
    if ctx.from_id in basically_gods:
        return True
    if not ctx.command:
        return True
    if not ctx.command.allowed_roles:
        return True
    if not isinstance(ctx.command.allowed_roles, list):
        return False
    try:
        prof = await FCMember.load(ctx.from_id)
    except ProfileNotCreatedError:
        return False
    return await prof.solve_role(ctx, ctx.command.allowed_roles)


@fcbot.check
async def chat_check(ctx):
    if ctx.peer_id not in chatlist and ctx.from_id not in basically_gods:
        await ctx.send(answers['warnings']['not_in_chatlist'])
        return False
    return True


@fcbot.listen()
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        msg = ctx.invoked_with + deepcopy(ctx.view).read_rest()
        msg = msg.lower()
        poss = []
        for comm in fcbot.commands:
            for alias in [comm.name] + comm.aliases:
                if not comm.hidden and fuzz.partial_ratio(msg, alias) >= 80:
                    poss.append(alias)
                    break
        ans = answers['warnings']['command_misspelled']
        if poss and len(poss) <= 5:
            ans += answers['misc']['command_suggestions'].format(', '.join(poss))
        await ctx.send(ans)
    elif isinstance(error, FConversionError):
        return await ctx.send(error.msg)
    elif isinstance(error, BadArgument):
        return await ctx.send(answers['warnings']['bad_argument'].format(ctx.prefix, ctx.command.usage))
    elif isinstance(error, MissingRequiredArgument):
        return await ctx.send(answers['warnings']['missing_argument'].format(ctx.prefix, ctx.command.usage))
    elif isinstance(error, ProfileNotCreatedError):
        return await ctx.send(error.original)
    elif isinstance(error, CommandOnCooldown):
        wt = math.ceil(error.retry_after)
        return await ctx.send(answers['warnings']['command_on_cooldown'].format(wt, form(wt, ["секунду", "секунды", "секунд"])))
    elif isinstance(error, CommandInvokeError):
        traceback.print_exception(type(error), error, error.__traceback__)
        await log_error(ctx.message.original_data, ''.join(traceback.format_exception(type(error), error, error.__traceback__)))
        if len(str(error.original)) < 200 and 'access_token' not in str(error.original):
            await ctx.send(answers['warnings']['other_error'].format(error.original))
        else:
            await ctx.send(answers['warnings']['other_error'].format('(подробнее в логах)'))
        for prof in profiles_cache:
            await profiles_cache[prof].dump()

fcbot.run(vk_fcbot_beta_token if dev else vk_fcbot_token)
