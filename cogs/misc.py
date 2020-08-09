from vk_botting import Cog, Keyboard, KeyboardColor
from random import choice

from cogs.general import *


class Misc(Cog):
    def __init__(self):
        fcbot.loop.create_task(self.limits_reset_loop())

    @staticmethod
    async def limits_reset_loop():
        while True:
            try:
                dtn = datetime.now()
                if dtn.hour == 0 and dtn.minute == 0 and dtn.second <= 5:
                    await abstract_sql('UPDATE limits SET used=0 WHERE used>0')
                    await sleep(10)
                else:
                    await sleep(time_until_time(0, 0, 0))
            except Exception as e:
                print(f'Exception in limits_reset_loop: {e}')

    @command(name='колесо удачи', aliases=['колесо'], used_art='fortune_wheel',
             help='Команда для вращения колеса фортуны\nВозможные награды:\n• 100 печенек\n• 1 печенька\n• +5 к статусу\n• Ничего')
    async def fortune_wheel(self, ctx):
        prof = await FCMember.load(ctx.from_id)
        if prof.cookies < fortune_wheel_cost:
            return await ctx.send(answers['warnings']['not_enough_cookies'])
        prof.cookies -= fortune_wheel_cost
        await prof.dump()
        reward, value = choice(fortune_wheel_rewards)
        return await ctx.send(await fortune_solvers[reward](ctx.from_id, value))

    @command(name='выбери', aliases=['реши', 'выбор', 'выбери,', 'реши,'], usage='выбери <варианты разделенные через запятую или "или">',
             help='Эту команду можно использовать, если не знаете, что выбрать\nПример использования: выбери спать, есть или все же спать')
    async def choose(self, ctx, *, choices: str):
        variants = split(choices, (',', 'или'))
        if len(variants) <= 1:
            return await ctx.send(answers['warnings']['too_few_variants'])
        return await ctx.send(answers['confirmations']['i_choose'].format(choice(variants)))

    @command(name='шанс', aliases=['проценты', 'вероятность'], usage='шанс <событие>',
             help='Команда, которая очень точно считает шанс определенного события')
    async def get_percentage(self, ctx, *, _):
        return await ctx.send(answers['confirmations']['percentage'].format(randint(0, 100)))

    @command(name='кто', aliases=['кого', 'кому', 'кем', 'о ком'], used_art='who',
             help='Команда, которая точно укажет на человека по описанию')
    async def who(self, ctx):
        target = await fcbot.get_random_member(ctx.peer_id)
        ment = await fcbot.get_display_name(target)
        user = await fcbot.get_user(target, fields='photo_id')
        if not user.photo_id:
            att = await fcbot.get_random_art(ctx.command.used_art)
        else:
            att = 'photo' + user.photo_id
        return await ctx.send(answers['confirmations']['who'].format(ment), attachment=att)

    @command(name='обнять', used_art='hug', income=1, usage='обнять [цель]',
             help='Обнимашки c:\n(в случае если не указана цель, обнимает случайного пользователя)')
    async def hug(self, ctx, *, target=''):
        if not target:
            rand = await fcbot.get_random_member(ctx.peer_id)
            target = await fcbot.get_mention(rand)
        ment = await fcbot.get_mention(ctx.from_id)
        gend = await fcbot.get_gender_end(ctx.from_id)
        return await ctx.send(answers['confirmations']['hug'].format(ment, gend, target))

    @command(name='успокоить', used_art='calmdown', income=3, usage='успокоить <цель>',
             help='Команда, чтобы успокоить пользователя')
    async def calmdown(self, ctx, *, target):
        ment = await fcbot.get_mention(ctx.from_id)
        gend = await fcbot.get_gender_end(ctx.from_id)
        return await ctx.send(answers['confirmations']['calmdown'].format(ment, gend, target))

    @command(name='погладить', aliases=['гладить'], used_art='pat', income=5, usage='погладить [цель]',
             help='Позволяет погладить кого-либо\n(в случае если не указана цель, гладит случайного пользователя)')
    async def pat(self, ctx, *, target=''):
        if not target:
            rand = await fcbot.get_random_member(ctx.peer_id)
            target = await fcbot.get_mention(rand)
        ment = await fcbot.get_mention(ctx.from_id)
        gend = await fcbot.get_gender_end(ctx.from_id)
        return await ctx.send(answers['confirmations']['pat'].format(ment, gend, target))

    @command(name='помощь', aliases=['команды'],
             usage='помощь [команда]', help='Если ты читаешь это сообщение, то, думаю, ты понимаешь для чего эта команда')
    async def help(self, ctx, *, comm=''):
        if not comm:
            keyboard = Keyboard(inline=True)
            cats = ['Основные команды', 'Команды профилей', 'Команды семьи', 'Команды администрации']
            for cat in cats:
                keyboard.add_button(cat, KeyboardColor.SECONDARY)
                keyboard.add_line()
            keyboard.lines.pop(-1)
            return await ctx.send('Категории команд:\n' + '\n'.join(cats), keyboard=keyboard)
        res = command_converter(comm)
        if res.help:
            return await ctx.send(answers['confirmations']['help'].format(res.name, ctx.prefix, res.usage, res.help))
        return await ctx.send(answers['confirmations']['short_help'].format(res.name, ctx.prefix, res.usage))

    @command(name='основные команды', aliases=['основные', 'помощь основные', 'команды основные'])
    async def main_help(self, ctx):
        lines = ['Основные команды:', 'Колесо удачи', 'Кто', 'Выбери', 'Шанс', 'Обнять', 'Погладить', 'Успокоить']
        for comm in fcbot.commands:
            if comm.callback_instance:
                lines.append(comm.name.capitalize())
        return await ctx.send('\n'.join(lines))

    @command(name='команды профилей', aliases=['помощь профилей', 'помощь по профилю', 'помощь по профилям', 'помощь профиля',
                                               'команды профиля', 'команды для профиля'])
    async def profile_help(self, ctx):
        return await ctx.send('Команды профилей:\nПрофиль\nНик\nПодарить печеньки')

    @command(name='команды семьи', aliases=['помощь семьи', 'помощь по семье', 'помощь семей', 'команды семей'])
    async def family_help(self, ctx):
        prof = await FCMember.load(ctx.from_id)
        fam = await prof.get_family()
        lines = ['Команды семей:', 'Семья']
        if fam.partner:
            lines.append('Развод')
            lines.append('Завести ребенка')
        else:
            if await prof.get_outgoing_request():
                lines.append('Отменить запрос')
            else:
                lines.append('Предложение')
            if await prof.get_incoming_request():
                lines.append('Отклонить запрос')
                lines.append('Принять запрос')
        if await fam.get_children():
            lines.append('Сдать в детдом')
        if await fam.get_parents():
            lines.append('Сбежать от родителей')
        elif await fam.get_parents(True):
            lines.append('Стать ребенком')
            lines.append('Не хочу быть ребенком')
        return await ctx.send('\n'.join(lines))

    @command(name='команды администрации', aliases=['помощь администрации', 'помощь админа', 'помощь админов',
                                                    'помощь для админов', 'команды админа', 'команды админов'])
    async def admin_help(self, ctx):
        lines = ['Команды администрации:']
        mod_commands = fcbot.get_cog('Moderation').get_commands()
        prof = await FCMember.load(ctx.from_id)
        for comm in mod_commands:
            if comm.allowed_roles:
                if prof.id in basically_gods or await prof.solve_role(ctx.peer_id, comm.allowed_roles):
                    lines.append(comm.name.capitalize())
        return await ctx.send('\n'.join(lines) if len(lines) > 1 else answers['confirmations']['no_admin_commands'])


def misc_setup():
    fcbot.add_cog(Misc())
