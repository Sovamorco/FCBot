import os
from json import dumps
from random import randint
from typing import List

import git
import regex as re
import vk_botting
from vk_botting import Bot, BadArgument, Command, when_mentioned_or_pm_or, ConversionError
from vk_botting.conversions import Converter

from cogs.abstract import *


class FCMember(AbstractSQLObject):
    _table = 'users'
    _key_column = 'id'
    id: int
    nick: str

    async def get_mention(self):
        if self.nick:
            return f'[id{self.id}|{self.nick}]'
        user = await self.bot.get_user(self.id)
        return user.mention

    # noinspection PyProtectedMember
    @property
    def bot(self) -> 'FCBot':
        return type(self)._bot

    @classmethod
    async def load(cls, uid):
        if uid in profiles_cache:
            return profiles_cache[uid]
        res = await cls.select(uid)
        if not res:
            raise ProfileNotCreatedError(f'Профиль пользователя {uid} не создан!')
        if uid in profiles_cache:
            return profiles_cache[uid]
        profiles_cache[uid] = res
        return res

    async def get_roles(self) -> 'List[Role]':
        res = await abstract_fetch(True, 'roles', ['id'], [self.id])
        return [Role(data) for data in res]

    async def get_chat_roles(self, chat_id) -> 'List[Role]':
        roles = await self.get_roles()
        return [role for role in roles if role.scope in [chat_id, 0]]

    async def solve_role(self, chat_id, roles) -> bool:
        roles = roles.copy()
        for role in roles.copy():
            if isinstance(role, int):
                if self.id == role:
                    return True
                roles.remove(role)
        chat_roles = await self.get_chat_roles(chat_id)
        return any(role.name in roles for role in chat_roles)

    async def has_role(self, role_name, chat_id):
        roles = await self.get_chat_roles(chat_id)
        return any(role_name == role.name for role in roles)

    async def add_role(self, role, chat_id):
        if await self.has_role(role, chat_id):
            return False
        scope = chat_id * role_scopes[role]
        await abstract_sql('INSERT INTO roles (id, role, scope) VALUES (%s, %s, %s)', self.id, role, scope)
        return True

    async def remove_role(self, role, chat_id):
        if not await self.has_role(role, chat_id):
            return False
        scope = chat_id * role_scopes[role]
        await abstract_sql('DELETE FROM roles WHERE id=%s AND role=%s AND scope=%s', self.id, role, scope)
        return True


class FCBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.global_cooldown_bucket = {}
        self.messages_cache = {}
        self.bottle_cache = {}
        self.album_converter = {}
        self.global_cooldown_rate = 60
        self.global_cooldown_count = 2
        self.spam_length_threshold = 7
        self.spam_time_threshold = 7
        self.spam_count_threshold = 4
        self.quick_spam_time_threshold = 4
        self.quick_spam_count_threshold = 4

    async def uid(self, screen_name, ignorant=False):
        if isinstance(screen_name, int):
            return screen_name
        elif screen_name.isdigit():
            user = 'id' + screen_name
        else:
            match = re.match(vk_id_regex, screen_name)
            if match:
                user = match.group(1) or 'id' + match.group(2)
            else:
                user = screen_name
        result = await self.vk_request('utils.resolveScreenName', screen_name=user)
        if 'response' not in result or not result['response'] or 'object_id' not in result['response']:
            if ignorant:
                return None
            raise BadArgument
        return result['response']['object_id']

    async def get_display_name(self, uid):
        try:
            prof = await FCMember.load(uid)
            if prof.nick:
                return prof.nick
        except ProfileNotCreatedError:
            pass
        user = await self.get_user(uid)
        return user.first_name

    async def get_mention(self, uid):
        nick = await self.get_display_name(uid)
        return f'[id{uid}|{nick}]'

    async def hello_from_pinned(self, peer_id):
        chat = await self.vk_request('messages.getConversationsById', peer_ids=peer_id)
        if 'response' in chat.keys() and chat['response']['items'] and 'pinned_message' in chat['response']['items'][0]['chat_settings']:
            ans = '\n' + chat['response']['items'][0]['chat_settings']['pinned_message']['text']
        else:
            ans = 'Добро пожаловать'
        return ans

    async def create_album(self, title, description):
        res = await self.user_vk_request('photos.createAlbum', group_id=self.group.id, title=title, description=description, upload_by_admins_only=1)
        if 'response' not in res:
            print(f'Ошибка при создании альбома! Ответ сервера: {res}')
        return res['response']['owner_id'], res['response']['id']

    async def get_album(self, comm):
        oid, aid = self.album_converter[comm]
        res = await self.user_vk_request('photos.get', owner_id=oid, album_id=aid, count=1000)
        images = res['response']['items']
        if 'error' in res:
            return []
        if res['response']['count'] > 1000:
            for i in range(1000, res['response']['count'], 1000):
                tr = await self.user_vk_request('photos.get', owner_id=oid, album_id=aid, count=1000, offset=i)
                if 'response' in tr:
                    images += tr['response']['items']
        images = ['https://vk.com/photo{owner_id}_{id}'.format(**image) for image in images]
        return images

    async def get_albums(self):
        albums = {}
        for comm in self.album_converter:
            oid, aid = self.album_converter[comm]
            if oid not in albums:
                albums[oid] = []
            albums[oid].append(aid)
        result = {}
        for owner in albums:
            res = await self.user_vk_request('photos.getAlbums', owner_id=owner, album_ids=albums[owner])
            if 'response' not in res:
                continue
            for album in res['response']['items']:
                result[album['title']] = album['size']
        return result

    async def get_random_art(self, key):
        if key not in self.album_converter:
            return None
        oid, aid = self.album_converter[key]
        fst = await self.user_vk_request('photos.get', owner_id=oid, album_id=aid, count=0)
        if 'error' in fst or fst['response']['count'] < 1:
            return None
        rand = randint(0, fst['response']['count'] - 1)
        res = await self.user_vk_request('photos.get', owner_id=oid, album_id=aid, count=1, offset=rand)
        item = res['response']['items'][0]
        return 'photo{owner_id}_{id}'.format(**item)

    async def delete_arts(self, *links):
        results = []
        for link in links:
            oid, pid = link.replace('photo', '').split('_')
            res = await self.user_vk_request('photos.delete', owner_id=oid, photo_id=pid)
            if 'error' in res and res['error']['error_code'] == 100:
                results.append(None)
            else:
                results.append(link)
        if all(result is None for result in results):
            return None
        return [result for result in results if result is not None]

    async def kick(self, chat_id, member_id):
        if chat_id > 2000000000:
            chat_id -= 2000000000
        await self.vk_request('messages.removeChatUser', chat_id=chat_id, member_id=member_id)

    async def get_members(self, chat_id) -> dict:
        res = await self.vk_request('messages.getConversationMembers', peer_id=chat_id, fields='online')
        members = {}
        if 'response' not in res:
            return []
        for item in res['response']['items']:
            if item['member_id'] > 0:
                members[item['member_id']] = self.get_member_by_id(res['response']['profiles'], item['member_id'])
        return members

    async def change_status(self, text):
        await self.user_vk_request('status.set', group_id=self.group.id, text=text)

    async def get_gender_end(self, uid):
        res = await self.get_user(uid, fields=['sex'])
        return 'а' if res.sex == 1 else ''

    @staticmethod
    def get_member_by_id(profiles, member_id):
        for profile in profiles:
            if profile['id'] == member_id:
                return profile
        return {'id': member_id, 'first_name': 'Unknown', 'last_name': 'Unknown', 'online': 0}

    async def refresh_albums(self):
        res = await abstract_fetch(True, 'albums')
        self.album_converter = {}
        for comm in res:
            self.album_converter[comm['art']] = [comm['owner'], comm['album']]

    async def add_album(self, art, owner, album):
        await abstract_sql('INSERT INTO albums (art, owner, album) VALUES (%s, %s, %s)', art, owner, album)
        self.album_converter[art] = [owner, album]

    @staticmethod
    def get_new_commits():
        repo = git.Repo(os.getcwd())
        commits = repo.iter_commits(repo.active_branch)
        last_hex = get_last_commit()
        new_commits = []
        for commit in commits:
            if commit.hexsha == last_hex:
                break
            else:
                new_commits.append(commit)
        reset_last_commit(new_commits)
        return new_commits

    async def send_update_message(self):
        new = self.get_new_commits()
        if not new:
            await self.send_message(admin_chat, 'Бот запущен')
        else:
            ans = 'Бот обновлен.'
            if len(new) == 1:
                ans += f'\nТекст последнего обновления:'
            else:
                ans += f'\nОбновлений - {len(new)}'
                if len(new) > 5:
                    ans += '\nТексты последних пяти обновлений:'
                else:
                    ans += '\nТексты обновлений:'
            for commit in new[:5]:
                ans += f'\n\n--->{commit.message.strip()}'
            lines, insertions, deletions = zip(*[(comm.stats.total['lines'], comm.stats.total['insertions'], comm.stats.total['deletions']) for comm in new])
            lines, insertions, deletions = sum(lines), sum(insertions), sum(deletions)
            ans += f'\n\nИзмененных строк: {lines} (+{insertions}/-{deletions})'
            await self.send_message(admin_chat, ans, attachment=await self.get_random_art('update'))


class FCommand(Command):
    def __init__(self, *args, **kwargs):
        self.allowed_roles = kwargs.pop('allowed_roles', None)
        self.used_art = kwargs.pop('used_art', None)
        self.help = kwargs.pop('help', None)
        self.usage = kwargs.pop('usage', None)
        self.hidden = kwargs.pop('hidden', False)
        self.disable_global_cooldown = kwargs.pop('disable_global_cooldown', False)
        self.callback_instance = kwargs.pop('callback', None)
        super().__init__(*args, **kwargs)


async def log_message(dt, peer_id, user_id, msg):
    msgj = dumps(msg)
    dtf = dt.strftime('%Y-%m-%d %H:%M:%S')
    text = msg['text'] if msg['text'] else ''
    await abstract_sql('INSERT INTO `messages` (datetime, chat, user, text, message) VALUES (%s, %s, %s, %s, %s)', dtf, peer_id, user_id, text, msgj)


async def log_error(msg, error):
    msg = dumps(msg)
    await abstract_sql('INSERT INTO `errors` (message, error) VALUES (%s, %s)', msg, error)


def get_last_commit():
    try:
        return open('resources/latestcommit', 'r').read()
    except FileNotFoundError:
        return ''


def reset_last_commit(new_commits):
    if new_commits:
        open('resources/latestcommit', 'w+').write(new_commits[0].hexsha)


def command(*args, **kwargs):
    return vk_botting.command(*args, **kwargs, cls=FCommand)


class Role:
    def __init__(self, data):
        self.name = data['role']
        self.scope = data['scope']


def form(num, arr):
    if 15 > abs(num) % 100 > 10:
        return arr[2]
    if abs(num) % 10 == 1:
        return arr[0]
    if abs(num) % 10 > 4 or abs(num) % 10 == 0:
        return arr[2]
    return arr[1]


def trim_image_url(screen_name):
    res = re.search(art_regex, screen_name) or re.search(doc_regex, screen_name)
    if not res:
        return None
    return res.group()


class IDConverter(Converter):
    async def convert(self, _, argument):
        return await fcbot.uid(argument)


def role_converter(arg: str):
    arg = arg.lower()
    for role in roles_conv:
        for alias in roles_conv[role]:
            if arg.startswith(alias):
                return role
    return None


class CallbackCommand:
    def __init__(self, id_, text, art):
        self.id = id_
        self.text = text
        self.art = art
        self.aliases = []
        self.name = ''

    @classmethod
    async def check_name(cls, name) -> bool:
        res = await abstract_fetch(True, 'command_aliases', ['alias'], [name])
        return bool(res)

    @classmethod
    async def add(cls, name, text, art):
        if await cls.check_name(name):
            return None
        row_id = await abstract_sql('INSERT INTO callbacks (text, art) VALUES (%s, %s)', text, art, last_row=True)
        await abstract_sql('INSERT INTO command_aliases (alias, command_id) VALUES (%s, %s)', name, row_id)
        if art not in fcbot.album_converter:
            oid, aid = await fcbot.create_album(name.capitalize(), f'Арты для команды "{name.capitalize()}"')
            await fcbot.add_album(art, oid, aid)
        res = cls(row_id, text, art)
        res.name = name
        return res

    async def get_aliases(self):
        res = await abstract_fetch(True, 'command_aliases', ['command_id'], [self.id], ['alias'])
        self.aliases = [alias['alias'] for alias in res]
        self.name = self.aliases.pop(0)

    def inject(self):
        fcbot.add_command(FCommand(name=self.name, aliases=self.aliases, func=self.callback, used_art=self.art, callback=self))

    async def update(self):
        fcbot.remove_command(self.name)
        await self.get_aliases()
        self.inject()

    async def add_alias(self, alias):
        if await type(self).check_name(alias):
            return False
        await abstract_sql('INSERT INTO command_aliases (alias, command_id) VALUES (%s, %s)', alias, self.id)
        await self.update()
        return True

    @staticmethod
    async def convert_callback_text(text: str, ctx, msg):
        if '{ment}' in text:
            ment = await fcbot.get_mention(ctx.from_id)
            text = text.replace('{ment}', ment)
        if '{msg}' in text:
            text = text.replace('{msg}', msg)
        args = msg.split()
        for i, arg in enumerate(args):
            if f'{{arg{i+1}}}' in text:
                text = text.replace(f'{{arg{i+1}}}', arg)
        return text

    async def callback(self, ctx, *, msg=''):
        res = await self.convert_callback_text(self.text, ctx, msg)
        return await ctx.send(res, attachment=await fcbot.get_random_art(self.art))

    async def delete(self):
        fcbot.remove_command(self.name)
        await abstract_sql('DELETE FROM command_aliases WHERE command_id=%s', self.id)
        await abstract_sql('DELETE FROM callbacks WHERE some_id=%s', self.id)


async def get_callbacks():
    callbacks = await abstract_fetch(True, 'callbacks')
    res = []
    for callback in callbacks:
        temp = CallbackCommand(callback['some_id'], callback['text'], callback['art'])
        await temp.get_aliases()
        res.append(temp)
    return res


async def inject_callbacks():
    callbacks = await get_callbacks()
    for callback in callbacks:
        callback.inject()


class CommandConverter(Converter):
    async def convert(self, ctx, argument):
        value = argument.lower()
        for comm in fcbot.walk_commands():
            if value in [comm.name] + comm.aliases:
                return comm
        await ctx.send('Нет команды с таким названием!')
        raise ConversionError


fcbot = FCBot(when_mentioned_or_pm_or('!'), case_insensitive=True)
profiles_cache = AbstractCacheManager(fcbot.loop, 900)