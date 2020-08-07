from credentials import dev, sql_user, sql_password
from cogs.utils import *

host = '192.168.1.5' if dev else '127.0.0.1'
config = {'host': host, 'user': sql_user, 'password': sql_password, 'db': 'fcbot', 'autocommit': True}

art_regex = r'photo-?[0-9]+_[0-9]+'
doc_regex = r'doc-?[0-9]+_[0-9]+'
all_regex = r'[*@](all|online|все|алл|онлайн)([^a-zA-Z1-9а-яА-Я_]|$)'
vk_id_regex = r'(?:https?:\/\/)?(?:www\.)?(?:m\.)?vk.com\/([^\n ]+)|\[id([0-9]+)\|.+]'

admin_chat = 2000000001

first_hedgehog = 576971572
second_hedgehog = 605829137
not_a_hedgehog = 444055684
basically_gods = [first_hedgehog, second_hedgehog, not_a_hedgehog]
chatlist = [admin_chat]

child_limit = 4

role_scopes = {
    'программист': False,
    'создатель': False,
    'админ': [12345]
}
valid_roles = list(role_scopes.keys())

roles_conv = {
    'админ': ['админ', 'адм', 'adm'],
    'программист': ['программист', 'разр', 'прог', 'prog', 'razr'],
    'создатель': ['создатель', 'созд', 'sozd']
}

answers = {
    'confirmations': {
        'general': 'Готово!',
        'art': 'Готово! Добавленный арт:',
        'arts': 'Готово!\nДобавленные арты:',
        'arts_deleted': 'Готово! Удаленные арты:\n',
        'exec': ':)',
        'arts_count': 'Количество артов различных команд:\n',
        'help': 'Команда "{}":\nИспользование: {}{}\n\nСправка: "{}"',
        'kicked_for_warnings': 'Пользователь исключен за полученные предупреждения!',
        'wedding': 'Типа текст свадьбы {} и {}\n(Тут могла быть ваша реклама)',
        'divorce': 'Типа текст развода {} и {}',
        'child_requested': 'Готово! Ребенок должен подтвердить свое существование командой "{0}стать ребенком"! или если он не хочет быть ребенком, написать "{0}не хочу быть ребенком"!',
        'fortune_wheel': {
            'no_reward': '{} вращает колесо и... {} ничего не выпадает. Ничего, повезет в следующий раз.',
            'general': '{} вращает колесо и... {} выпадает {} {}'
        },
        'i_choose': 'Я выбираю "{}"',
        'percentage': 'Я думаю что это произойдет с шансом в {}%',
        'who': 'Я думаю это {}!',
        'hug': '{} обнял{} {}',
        'calmdown': '{} успокоил{} {}',
        'pat': '{} погладил{} {}'
    },
    'warnings': {
        'wrong_role': f'Неверно написана роль. Список доступных ролей: {", ".join(role.capitalize() for role in valid_roles)}',
        'wrong_command': 'Нет команды с таким названием!',
        'role_not_available': 'Эту роль нельзя выдавать в этой беседе!',
        'already_has_role': 'У пользователя уже есть эта роль!',
        'does_not_have_role': 'У пользователя нет этой роли!',
        'command_name_taken': 'Это название уже занято!',
        'cannot_name_command': 'Этой команде нельзя добавлять названия!',
        'cannot_delete_command': 'Эту команду нельзя удалить!',
        'attach_arts': 'Для добавления артов прикрепите их к сообщению',
        'wrong_image_url': 'Некорректная ссылка на арт!',
        'no_such_arts': 'Таких артов не существует!',
        'no_command_arts': 'Нет артов для данной команды!',
        'profile_not_created': 'Профиль пользователя {} не создан!\nДля создания профиля пользователь должен написать хотя бы одно сообщение',
        'not_in_chatlist': 'Команды можно использовать только в беседах [club151434682|Фандомной Кафешки]!',
        'command_misspelled': 'Неверно написана команда или ее не существует',
        'bad_argument': 'Неверный тип аргумента\nПример использования: "{}{}"',
        'missing_argument': 'Пример использования: "{}{}"',
        'command_on_cooldown': 'Команда перезаряжается, подождите {} {}',
        'other_error': f'Ошибка:\n{{}}\n[id{second_hedgehog}|_]',
        'no_warnings': 'У этого пользователя нет предупреждений!',
        'family': {
            'sent_request': 'Вы уже отправили запрос на брак!',
            'already_married': 'Вы уже состоите в браке!'
        },
        'bad_nickname_size': 'Длина ника должна быть от 1 до 25 символов!',
        'bad_nickname_symbols': 'Ник не может содержать квадратные скобки, символ |, символ $ или переносы строк, не может кончаться на ":" или "-"!',
        'no': 'Нет',
        'proposal': {
            'no_selfcest': 'Увы, так не получится',
            'already_married': 'Вы уже состоите в браке!',
            'active_outgoing_request': 'Вы уже отправили запрос!\nНапишите "{}отменить", чтобы отменить его',
            'target_already_married': 'Пользователь уже состоит в браке!',
            'active_incoming_request': 'Пользователю уже отправили запрос!',
            'no_incest': 'Нельзя вступать в брак с родственниками или возможными родственниками!'
        },
        'no_incoming_request': 'Вам не отправляли запрос!',
        'no_outgoing_request': 'Вы не отправляли запрос!',
        'not_married': 'Вы не в браке!',
        'child': {
            'already_have_parents': 'У вас уже есть родители!',
            'no_request': 'Вам не предлагали стать ребенком!',
            'too_many_children': f'У ваших родителей уже есть {child_limit} {sform(child_limit, "ребенок")}',
            'no_parents': 'У вас нет родителей!'
        },
        'not_your_child': 'Пользователь не ваш ребенок!',
        'too_many_children': f'У вас уже есть {child_limit} {sform(child_limit, "ребенок")}',
        'already_has_parents': 'У данного ребенка уже есть родители!',
        'already_requested': 'Данного ребенка уже запросили!\nОн должен согласиться быть ребенком, написав "{0}стать ребенком" или отказаться, написав "{0}не хочу быть ребенком"!',
        'dangerous_child': 'Нельзя делать детьми своих родственников или возможных родственников!',
        'bad_posint': 'Число не может быть меньше или равно нулю!',
        'not_enough_cookies': 'У вас не хватает печенек!',
        'noattr': 'У профилей пользователя нет такого аттрибута!',
        'too_few_variants': 'Тут нечего выбирать'
    },
    'misc': {
        'greeting': 'Добро пожаловать!',
        'bot_launched': 'Бот запущен!',
        'bot_updated': {
            'main': 'Бот обновлен.',
            'one_update': '\nТекст последнего обновления:',
            'multiple_updates': '\nОбновлений - {}',
            'less_than_five': '\nТексты обновлений:',
            'more_than_five': '\nТексты последних пяти обновлений:',
            'commit': '\n\n--->{}',
            'lines': '\n\nИзмененных строк: {} (+{}/-{})'
        },
        'command_suggestions': '\nВозможно вы имели в виду: {}',
        'cookies': ['печенька', 'печеньки', 'печенек'],
        'pronouns': ['ему', 'ей']
    },
    'profiles': {
        'profile': {
            'header': 'Профиль {}:',
            'warnings': 'Предов - {}',
            'role': 'Роль - {}',
            'cookies': 'Печенек - {}',
            'invited': 'Первый день - {}',
            'disclaimer': '(Это временный профиль без оформления ибо оформлением я буду заниматься в самом конце)'
        },
        'family': {
            'header': 'Семья {}:',
            'parents': ['Нет родителей', 'Родители: {} и {}'],
            'partner': ['Не в браке', 'В браке с {}'],
            'children': ['Нет детей', 'Дочь - {}', 'Сын - {}'],
            'siblings': ['Нет братьев и сестер', 'Сестра - {}', 'Брат - {}']
        }
    }
}

fortune_wheel_cost = 40
fortune_wheel_rewards = {
    ('cookies', 1),
    ('cookies', 100),
    ('status', 5),
    ('nothing', None),
    ('nothing', None)
}

income_limit = 10
