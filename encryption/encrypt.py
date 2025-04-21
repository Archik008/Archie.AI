import hmac
import hashlib
import json
from urllib.parse import unquote

from configure.pyconfig import MAIN_BOT_TOKEN, DEV_BOT_TOKEN

def is_safe(init_data: str) -> bool:
    for bot_token in [MAIN_BOT_TOKEN, DEV_BOT_TOKEN]:
        checksum, sorted_init_data, user_value = convert_init_data(init_data)

        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        
        # Вычисляем хеш данных
        hash_value = hmac.new(secret_key, sorted_init_data.encode(), hashlib.sha256).hexdigest()

        result_verify = hmac.compare_digest(hash_value, checksum)

        if result_verify:
            return result_verify, user_value
        
    return None, None


def convert_init_data(init_data: str):
    # Разбираем initData в список key=value
    init_data_list = unquote(init_data).split('&')
    
    # Ищем hash и удаляем его из данных
    hash_value = ''
    user_value = None
    filtered_data = []
    for item in init_data_list:
        if item.startswith('hash='):
            hash_value = item.replace('hash=', '')
        else:
            if item.startswith('user='):
                user_value = json.loads(item.replace('user=', '')).get('id')
            filtered_data.append(item)
    
    # Сортируем данные в алфавитном порядке
    filtered_data.sort()
    
    # Объединяем данные в одну строку через \n (как в PHP)
    sorted_init_data = "\n".join(filtered_data)
    
    return hash_value, sorted_init_data, user_value