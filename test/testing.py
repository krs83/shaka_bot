import hashlib
import requests
import phpserialize
import urllib.parse

from b_soup import parsing, find_matching_fights

API_SECRET = 'df234DFmdd58GldjDMdgk84nd'
event_id = '446'
# event_id = '1339'
# event_id = '1169'
event_user_id = '443280'
server_url = 'https://shakasports.com'


# mode = 'event_info'
# mode = 'event_user'
# mode = 'event_info&event_user_id='
# mode = 'register'
# mode = 'list'
# mode = 'brackets'
# mode = 'schedule'

###########################################################
# подготовка к хешированию
def md5_hash(data):
    return hashlib.md5(data.encode()).hexdigest()


# Создание строки для хеширования
form_query_string = f'mode=event_info&id={event_id}&{API_SECRET}'
reg_query_string = f'mode=schedule&id={event_id}&{API_SECRET}'

# Вычисление MD5 хеша
form_hash_value = md5_hash(form_query_string)
reg_hash_value = md5_hash(reg_query_string)

##############################################################
# декодирование данных из PHP в json
form_url = f'{server_url}/pub/api.php?mode=event_info&id={event_id}&hash={form_hash_value}'
form_response = requests.get(form_url)
form_result = form_response.text


def decode_bytes(data):
    if isinstance(data, dict):
        return {decode_key(key): decode_bytes(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [decode_bytes(item) for item in data]
    elif isinstance(data, bytes):
        return data.decode('utf-8')
    else:
        return data


def decode_key(key):
    if isinstance(key, bytes):
        return key.decode('utf-8')
    return key  # Возвращаем ключ без изменений, если это не байтовая строка


# Десериализация
form_data = phpserialize.loads(form_result.encode('utf-8'))

# Декодирование данных
event_info = decode_bytes(form_data)

######################################################################
# формирование данных для отправки POST запроса

rules = event_info['rules']
age_divs = rules['age_divisions']
team = event_info['team_hash']
age_id = list(age_divs.keys())[7]

sex = list(age_divs[age_id]['sex_divisions'].keys())[1]
division_id = list(age_divs[age_id]['belt_divisions'].keys())[0]
weight_id = list(age_divs[age_id]['weights'].keys())[3]
team = list(event_info['team_hash'].keys())[112]
name = 'Еремеевская Марина'
email = 'marina@mail.ru'
tel = '+79591895020'

form = {
    'name': name,
    'email': email,
    'tel': tel,
    'age_division': age_id,
    'sex': sex,
    'division_id': division_id,
    'weight_division': weight_id,
    'team_id': team,
}
forms = phpserialize.dumps(form)

postdata = urllib.parse.urlencode({'form': form})

headers = {

    'header': 'Content-type: application/x-www-form-urlencoded',


}

reg_url = f'{server_url}/pub/api.php?mode=schedule&id={event_id}&hash={reg_hash_value}'
reg_response = requests.post(url=reg_url, headers=headers, data=postdata)
reg_result = reg_response.text
reg_data = phpserialize.loads(reg_result.encode('utf-8'))

# print(form)
# print(reg_data)
# print(reg_result)
fighters = parsing(reg_result)

while True:

    user_word = input("Введите слово для поиска (или 'q' для выхода): ")
    if user_word.lower() == 'q':
        break

    find_matching_fights(user_word, fighters)

# print(forms)
# print(postdata)

# print(event_info)

# 110 - "3814":"AF ACADEMY",
# 111 - "10480":"AF Academy (Луганск восток)",
# 112 - "10478":"AF Academy (Луганск ГС)",
# 113 - "10479":"AF Academy (Луганск Мирный)",
# 114 - "10481":"AF Academy (Луганск ОР)",
