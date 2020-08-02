from credentials import dev, sql_user, sql_password

host = '192.168.1.5' if dev else '127.0.0.1'
config = {'host': host, 'user': sql_user, 'password': sql_password, 'db': 'fcbot', 'autocommit': True}

art_regex = r'photo-?[0-9]+_[0-9]+'
doc_regex = r'doc-?[0-9]+_[0-9]+'
vk_id_regex = r'(?:https?:\/\/)?(?:www\.)?(?:m\.)?vk.com\/([^\n ]+)|\[id([0-9]+)\|.+]'

admin_chat = 2000000001

first_hedgehog = 576971572
second_hedgehog = 605829137
not_a_hedgehog = 444055684
basically_gods = [second_hedgehog, first_hedgehog, not_a_hedgehog]
chatlist = [admin_chat]

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
        'help': 'Команда "{}":\nИспользование: {}{}\n\nПомощь: "{}"',
        'kicked_for_warnings': 'Пользователь исключен за полученные предупреждения!'
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
        }
    },
    'misc': {
        'greeting': 'Добро пожаловать!',
        'bot_launched': 'Бот запущен!',
        'bot_updated': {
            'main': 'Бот обновлен.',
            'one_update': '\nТекст последнего обновления:',
            'multiple_updates': '\nОбновлений - ',
            'less_than_five': '\nТексты обновлений:',
            'more_than_five': '\nТексты последних пяти обновлений:',
            'commit': '\n\n--->{}',
            'lines': '\n\nИзмененных строк: {} (+{}/-{})'
        },
        'command_suggestions': '\nВозможно вы имели в виду: {}'
    }
}
