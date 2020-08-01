from datetime import datetime

import aiohttp
from vk_botting import Cog, Photo

from cogs.general import *


class Moderation(Cog):
    def __init__(self, bot: FCBot):
        self.bot = bot

    async def upload_photo(self, server, *urls):
        try:
            async with aiohttp.ClientSession() as client:
                files = aiohttp.FormData()
                for i, url in enumerate(urls):
                    imbts = await client.get(url)
                    cnt = imbts.content_type
                    ext = cnt[6:]
                    imbts = await imbts.read()
                    files.add_field(f'file{i}', imbts, filename='temp{}.{}'.format(i, ext))
                res = await client.post(server, data=files)
                photos = await res.json(content_type='text/html')
            payload = {
                'album_id': photos['aid'],
                'group_id': photos['gid'],
                'server': photos['server'],
                'photos_list': photos['photos_list'],
                'hash': photos['hash']
            }
            res = await self.bot.user_vk_request('photos.save', **payload)
            uploaded = res['response']
            return [f'photo{file["owner_id"]}_{file["id"]}' for file in uploaded]
        except Exception:
            raise Exception('Произошла ошибка')

    async def upload_photos(self, comm, *atts):
        if not atts or not any(isinstance(att, Photo) for att in atts):
            return None
        oid, aid = self.bot.album_converter[comm]
        server = await self.bot.user_vk_request('photos.getUploadServer', group_id=-oid, album_id=aid)
        server = server['response']['upload_url']
        to_upload = []
        for att in atts:
            if isinstance(att, Photo):
                largest = max(att.sizes, key=lambda x: x.height + x.width)
                to_upload.append(largest.url)
        if len(to_upload) > 5:
            res = await self.upload_photo(server, *to_upload[:5])
            res += await self.upload_photo(server, *to_upload[5:])
        else:
            res = await self.upload_photo(server, *to_upload)
        return res

    @Cog.listener()
    async def on_chat_kick_user(self, msg):
        chat_id = msg.peer_id
        uid = msg.action.member_id
        await self.bot.kick(chat_id, uid)

    @Cog.listener('on_chat_invite_user')
    @Cog.listener('on_chat_invite_user_by_link')
    async def on_invite(self, msg):
        chat_id = msg.peer_id
        uid = msg.action.member_id or msg.from_id
        ment = await self.bot.get_mention(uid)
        text = await self.bot.hello_from_pinned(chat_id)
        res = f'{ment}, {text}'
        return await msg.send(res, attachment=await self.bot.get_random_art('privetstvie'))

    @Cog.listener()
    async def on_message_new(self, msg):
        await log_message(datetime.now(), msg.peer_id, msg.from_id, msg.original_data)
        if msg.peer_id in chatlist:
            try:
                await FCMember.load(msg.from_id)
            except ProfileNotCreatedError:
                prof = await FCMember.create_default(msg.from_id)
                await msg.send(f'мне лень думать сообщение но в общем у [id{prof.id}|тебя] теперь есть профиль да')

    @command(name='exec', usage='exec <код>', allowed_roles=['razr'],
             help='Команда для выполнения кода на стороне бота')
    async def exec_(self, ctx, *, code):
        exec(
            f'async def __ex(ctx, self): ' +
            ''.join(f'\n    {line}' for line in code.split('\n'))
        )
        result = await locals()['__ex'](ctx, self)
        if result is None:
            result = ':)'
        return await ctx.send(result)

    @command(name='+роль', usage='+роль <роль> <id>', help='Команда для добавления роли пользователю', allowed_roles=True)
    async def add_role(self, ctx, role: role_converter, uid: IDConverter):
        if role not in valid_roles:
            return await ctx.send(f'Неверно написана роль. Список доступных ролей: {", ".join(role.capitalize() for role in valid_roles)}')
        if role_scopes[role] and ctx.peer_id not in role_scopes[role]:
            return await ctx.send('Эту роль нельзя выдавать в этой беседе!')
        prof = await FCMember.load(uid)
        res = await prof.add_role(role, ctx.peer_id)
        if not res:
            return await ctx.send('У пользователя уже есть эта роль!')
        return await ctx.send('Готово!')

    @command(name='-роль', usage='-роль <роль> <id>', help='Команда для удаления роли пользователя', allowed_roles=True)
    async def remove_role(self, ctx, role: role_converter, uid: IDConverter):
        if role not in valid_roles:
            return await ctx.send(f'Неверно написана роль. Список доступных ролей: {", ".join(role.capitalize() for role in valid_roles)}')
        if role_scopes[role] and ctx.peer_id not in role_scopes[role]:
            return await ctx.send('Эту роль нельзя выдавать в этой беседе!')
        prof = await FCMember.load(uid)
        res = await prof.remove_role(role, ctx.peer_id)
        if not res:
            return await ctx.send('У пользователя нет этой роли!')
        return await ctx.send('Готово!')

    @command(name='+команда', usage='+команда <название> <арт> <текст>', allowed_roles=True,
             help='Команда для добавления команд\nВ тексте {ment} автоматически заменяется на упоминание отправителя, '
                  'а {msg} на текст который он написал после команды (замены использовать не обязательно)\nЕсли название необходимо указать с пробелом, '
                  'оно должно быть в кавычках\nВ поле <арт> надо указать код для артов '
                  '(любое слово, если у нескольких команд код совпадает то у них будет общий набор артов)'
                  '\nПримеры использования:\n1. +команда кусь кусь {ment} укусил {msg}!\n'
                  '2. +команда "подарить шоколадку" шоколад {ment} подарил шоколадку {msg}!\n'
                  '3. +команда депрессия депрессия {ment} ушел в депрессию...\n'
                  '4. +команда "дай неко" неко Держи неко!')
    async def add_command(self, ctx, name, art, *, text):
        name = name.lower()
        art = art.lower()
        res = await CallbackCommand.add(name, text, art)
        if not res:
            return await ctx.send('Команда с таким именем уже существует!')
        res.inject()
        return await ctx.send('Готово!')

    @command(name='+название', usage='+название <команда> <название>', allowed_roles=True,
             help='Команда для добавления альтернативного названия команде, добавленной с помощью "+команда"\n'
                  'Пример: +название кусь укусить\n'
                  'После этого команду "кусь" можно будет так же использовать с помощью "укусить"')
    async def add_alias(self, ctx, comm: CommandConverter(), *, name):
        if not comm.callback_instance:
            return await ctx.send('Этой команде нельзя добавлять названия')
        callback = comm.callback_instance
        if await callback.add_alias(name.lower()):
            return await ctx.send('Готово!')
        return await ctx.send('Это название уже занято!')

    @command(name='-команда', usage='-команда <команда>', allowed_roles=True,
             help='Команда для удаления команд добавленных с помощью "+команда"')
    async def remove_command(self, ctx, *, comm: CommandConverter()):
        if not comm.callback_instance:
            return await ctx.send('Эту команду нельзя удалить')
        callback = comm.callback_instance
        await callback.delete()
        return await ctx.send('Готово!')

    @command(name='+арт', usage='+арт <команда>', allowed_roles=True,
             help='Команда для добавления арта команды\nДля добавления арта прикрепите его к сообщению')
    async def add_art(self, ctx, *, comm: CommandConverter()):
        if not ctx.message.attachments:
            return await ctx.send('Для добавления арта прикрепите его к сообщению')
        res = await self.upload_photos(comm.used_art, ctx.message.attachments[0])
        if not res:
            return await ctx.send('Для добавления арта прикрепите его к сообщению')
        return await ctx.send('Готово! Добавленный арт:', attachment=res)

    @command(name='+арты', usage='+арты <команда>', allowed_roles=True,
             help='Команда для добавления нескольких артов к команде\nДля добавления артов прикрепите их к сообщению')
    async def add_arts(self, ctx, *, comm: CommandConverter()):
        if not ctx.message.attachments:
            return await ctx.send('Для добавления артов прикрепите их к сообщению')
        res = await self.upload_photos(comm.used_art, *ctx.message.attachments)
        if not res:
            return await ctx.send('Для добавления артов прикрепите их к сообщению')
        return await ctx.send('Готово!\nДобавленные арты:', attachment=res)

    @command(name='-арт', usage='-арт <ссылка на арт>', allowed_roles=True,
             help='Команда для удаления арта из альбомов бота')
    async def remove_art(self, ctx, url):
        image = trim_image_url(url.lower())
        if not image:
            return await ctx.send('Некорректная ссылка на арт!')
        res = await self.bot.delete_arts(image)
        if res is None:
            return await ctx.send('Такого арта не существует!')
        return await ctx.send('Готово!')

    @command(name='-арты', usage='-арты <ссылки на арты>', allowed_roles=True,
             help='Команда для удаления нескольких артов из альбомов бота')
    async def remove_arts(self, ctx, *urls):
        images = [trim_image_url(url.lower()) for url in urls]
        images = [image for image in images if image is not None]
        res = await self.bot.delete_arts(*images)
        if res is None:
            return await ctx.send('Таких артов не существует!')
        return await ctx.send('Готово! Удаленные арты:\n' + '\n'.join([f'https://vk.com/{image}' for image in res]))

    @command(name='арты', usage='арты <команда>', allowed_roles=True,
             help='Команда для просмотра всех артов команды')
    async def show_arts(self, ctx, *, comm: CommandConverter()):
        res = await self.bot.get_album(comm.used_art)
        if not res:
            return await ctx.send('Нет артов для данной команды!')
        return await ctx.send('\n'.join(res))

    @command(name='количество артов', aliases=['кол-во артов'], allowed_roles=True,
             usage='количество артов', help='Команда для просмотра количества артов для различных команд')
    async def artcount(self, ctx):
        albums = await self.bot.get_albums()
        res = [(k, albums[k]) for k in sorted(albums, key=lambda x: (albums[x], x))]
        return await ctx.send('Количество артов различных команд:\n' + '\n'.join([f'{art[0]} - {art[1]}' for art in res]))

    @command(name='помощь', aliases=['команды'], allowed_roles=True,
             usage='помощь [команда]', help='Если ты читаешь это сообщение, то, думаю, ты понимаешь для чего эта команда')
    async def help(self, ctx, *, comm=''):
        if not comm:
            return await ctx.send('Список команд (это временная помощь, не волнуйтесь):\n' + '\n'.join([comm.name for comm in sorted(fcbot.commands, key=lambda x: x.name)]))
        res = await CommandConverter().convert(ctx, comm)
        return await ctx.send(f'Команда "{res.name}":\nИспользование: {ctx.prefix}{res.usage}\n\nПомощь: "{res.help}"')


def moderation_setup(bot):
    bot.add_cog(Moderation(bot))
