from credentials import dev, sql_user, sql_password

host = '192.168.1.5' if dev else '127.0.0.1'
config = {'host': host, 'user': sql_user, 'password': sql_password, 'db': 'fcbot', 'autocommit': True}

art_regex = r'photo-?[0-9]+_[0-9]+'
doc_regex = r'doc-?[0-9]+_[0-9]+'
vk_id_regex = r'(?:https?:\/\/)?(?:www\.)?(?:m\.)?vk.com\/([^\n ]+)|\[id([0-9]+)\|.+]'

nobody = 605829137
basically_gods = [nobody]
chatlist = basically_gods

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
