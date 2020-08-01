import math
import traceback

from credentials import vk_fcbot_token, vk_personal_audio_token
from fuzzywuzzy import fuzz
from vk_botting import CommandNotFound, MissingRequiredArgument, CommandOnCooldown

from cogs.moderation import *

FCMember._bot = fcbot


@fcbot.listen()
async def on_ready():
    moderation_setup(fcbot)
    await inject_callbacks()
    await fcbot.refresh_albums()
    await fcbot.attach_user_token(vk_personal_audio_token)
    await fcbot.send_update_message()
    print(f'Logged in as {fcbot.group.name}')


@fcbot.check()
async def roles_check(ctx):
    if not ctx.command:
        return True
    if not ctx.command.allowed_roles:
        return True
    if not isinstance(ctx.command.allowed_roles, list):
        return ctx.from_id in basically_gods
    try:
        prof = await FCMember.load(ctx.from_id)
    except ProfileNotCreatedError:
        return False
    return await prof.solve_role(ctx, ctx.command.allowed_roles)


@fcbot.check()
async def chat_check(ctx):
    if ctx.peer_id not in chatlist and ctx.from_id not in basically_gods:
        await ctx.send('Команды можно использовать только в беседах [club151434682|Фандомной Кафешки]!')
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
                    poss.append(comm.name)
                    break
        ans = 'Неверно написана команда или ее не существует'
        if poss and len(poss) <= 5:
            ans += '\nВозможно вы имели в виду: ' + ', '.join(poss)
        await ctx.send(ans)
    elif isinstance(error, BadArgument):
        return await ctx.send(f'Неверный тип аргумента\nПример использования: "!{ctx.command.usage}"')
    elif isinstance(error, MissingRequiredArgument):
        return await ctx.send(f'Пример использования: "!{ctx.command.usage}"')
    elif isinstance(error, ProfileNotCreatedError):
        return await ctx.send(f'{error.original}\n'
                              'Для создания профиля пользователь должен написать хотя бы одно сообщение')
    elif isinstance(error, CommandOnCooldown):
        wt = math.ceil(error.retry_after)
        return await ctx.send(f'Команда перезаряжается, подождите {wt} {form(wt, ["секунду", "секунды", "секунд"])}')
    elif isinstance(error, CommandInvokeError):
        traceback.print_exception(type(error), error, error.__traceback__)
        await log_error(ctx.message.original_data, ''.join(traceback.format_exception(type(error), error, error.__traceback__)))
        if len(str(error.original)) < 200 and 'access_token' not in str(error.original):
            await ctx.send(f'Ошибка:\n{error.original}\n[id{nobody}|_]')
        else:
            await ctx.send(f'Ошибка (подробнее в логах)\n[id{nobody}|_]')
        for prof in profiles_cache:
            await profiles_cache[prof].dump()

fcbot.run(vk_fcbot_token)
