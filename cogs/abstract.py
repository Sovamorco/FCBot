from asyncio import sleep
from copy import deepcopy
from time import time

import aiomysql
from vk_botting import CommandInvokeError, ConversionError

from cogs.constants import *


async def abstract_sql(query, *params, fetch=False, fetchall=False, last_row=False):
    pool = await aiomysql.create_pool(**config)
    r = None
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, params)
            if fetchall:
                r = await cur.fetchall()
            elif fetch:
                r = await cur.fetchone()
            elif last_row:
                r = cur.lastrowid
    pool.close()
    await pool.wait_closed()
    return r


# noinspection SqlResolve
async def abstract_fetch(fetch_all, table, keys=None, keys_values=None, fields=None,
                         raw_keys='', order_by=None, order_desc=False, limit=None, schema=None, matches_all=True):
    if keys_values is None:
        keys_values = []
    fields = f'{", ".join(fields)}' if fields else '*'
    delim = ' AND ' if matches_all else ' OR '
    keys = ' WHERE ' + delim.join([f'`{key}`=%s' for key in keys]) if keys else ''
    if not keys and raw_keys:
        keys = ' WHERE ' + raw_keys
    elif raw_keys:
        keys = keys + delim + raw_keys
    table = f'`{table}`' if not schema else f'`{schema}`.`{table}`'
    if order_by:
        order = f' ORDER BY {order_by}' + ' DESC' if order_desc else f' ORDER BY {order_by}'
    else:
        order = ''
    if limit:
        limit = f' LIMIT {limit}'
    else:
        limit = ''
    statement = (f"SELECT {fields} FROM {table}{keys}{order}{limit}", *keys_values)
    return await abstract_sql(*statement, fetch=True, fetchall=fetch_all)


class MetaASO(type):
    @property
    def table(cls):
        return cls._table

    @property
    def key_column(cls):
        return cls._key_column


# noinspection SqlResolve
class AbstractSQLObject(metaclass=MetaASO):
    def __init__(self, data):
        self.original = deepcopy(data)
        self.original_attrs = set(data.keys())
        nested = self.nest_dict(data)
        for k, v in nested.items():
            setattr(self, k, v)

    def nest_dict(self, flat):
        result = {}
        for k, v in flat.items():
            self._nest_dict_rec(k, v, result)
        return result

    def _nest_dict_rec(self, k, v, out):
        k, *rest = k.split('_', 1)
        if rest:
            self._nest_dict_rec(rest[0], v, out.setdefault(k, {}))
        else:
            out[k] = v

    def flatten(self, d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    @property
    def current(self):
        return self.__dict__.copy()

    @property
    def incremental(self):
        return []

    def get_changed(self):
        org = self.original
        cur = self.flatten(self.current)
        res = []
        for key in self.original_attrs:
            if org[key] != cur[key]:
                if key in self.incremental:
                    res.append((key, cur[key]-org[key]))
                else:
                    res.append((key, cur[key]))
        return tuple(zip(*res)) or ()

    async def dump(self):
        new = self.get_changed()
        if not new:
            return False
        changed, values = new
        changes = ', '.join(changed)
        filler = ', '.join(['%s'] * len(changed))
        updates = ', '.join([f'`{change}`=`{change}`+%s' if change in self.incremental else f'`{change}`=%s' for change in changed])
        await abstract_sql(f'INSERT INTO `{type(self).table}` ({type(self).key_column}, {changes}) VALUES (%s, {filler}) ON DUPLICATE KEY UPDATE {updates}',
                           *[getattr(self, type(self).key_column)] + values * 2)
        return True

    @classmethod
    async def create_default(cls, key_value):
        await abstract_sql(f'INSERT INTO `{cls.table}` ({cls.key_column}) VALUES (%s) ON DUPLICATE KEY UPDATE {cls.key_column}=%s', key_value, key_value)
        return await cls.select(key_value)

    @classmethod
    async def select(cls, key_value):
        data = await abstract_fetch(False, cls.table, [cls.key_column], [key_value])
        if not data:
            return None
        return cls(data)


class AbstractCacheManager:
    def __init__(self, loop, cache_lifetime=None):
        self.cache = {}
        self.cache_lifetime = cache_lifetime
        loop.create_task(self.update_cache())

    async def update_cache(self):
        stime = 1
        while True:
            try:
                if not self.cache_lifetime:
                    break
                if self.cache:
                    closest = min(self.cache.keys(), key=lambda x: self.cache[x][1])
                    ts = self.cache[closest][1]
                    if time() >= ts:
                        self.cache.pop(closest, None)
                        continue
                    else:
                        stime = ts - time()
                else:
                    stime = self.cache_lifetime
            except Exception as e:
                print(f'Exception in update_cache: {e}')
                stime = 1
            finally:
                await sleep(stime)

    def __setitem__(self, key, value):
        self.cache[key] = [value, time()]

    def __getitem__(self, item):
        self.cache[item][1] = time()
        return self.cache[item][0]

    def __contains__(self, item):
        return item in self.cache

    def __iter__(self):
        return self.cache.__iter__()


class ProfileNotCreatedError(CommandInvokeError):
    pass


class FConversionError(ConversionError):
    def __init__(self, msg):
        self.msg = msg
