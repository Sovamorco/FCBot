from datetime import datetime, timedelta

import regex as re
from pymorphy2 import MorphAnalyzer
from pymorphy2.shapes import restore_capitalization

morph = MorphAnalyzer()


def form(num, arr):
    if 15 > abs(num) % 100 > 10:
        return arr[2]
    if abs(num) % 10 == 1:
        return arr[0]
    if abs(num) % 10 > 4 or abs(num) % 10 == 0:
        return arr[2]
    return arr[1]


def sform(num, word):
    parsed = morph.parse(word)[0]
    formed = parsed.make_agree_with_number(num).word
    restored = restore_capitalization(formed, word)
    return restored


def split(txt, seps):
    res = re.compile("|".join(seps), re.IGNORECASE).split(txt)
    return [el.strip() for el in res]


def time_until_time(hours, minutes, seconds):
    dtn = datetime.now()
    target = datetime(dtn.year, dtn.month, dtn.day, hours, minutes, seconds)
    if target < dtn:
        target += timedelta(days=1)
    return (target-dtn).total_seconds()
