import requests
import json
import os
import logging
import time
import http

from config import FOLDER_ID, TOKEN_PATH, LANG, VOICE, EMOTION, SPEED, URL


def create_new_token():

    metadata_url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {"Metadata-Flavor": "Google"}

    token_dir = os.path.dirname(TOKEN_PATH)
    if not os.path.exists(token_dir):
        os.makedirs(token_dir)

    try:
        response = requests.get(metadata_url, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            token_data['expires_at'] = time.time() + token_data['expires_in']
            with open(TOKEN_PATH, "w") as token_file:
                json.dump(token_data, token_file)
            logging.info("Token created")
        else:
            logging.error(f"Failed to retrieve token. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"An error occurred while retrieving token: {e}")


def check_token():

    with open(TOKEN_PATH, "r") as token_file:
        token_data = json.loads(token_file.read(), strict=False)

    if time.time() >= token_data['expires_in']:
        create_new_token()

    IAM_TOKEN = token_data['access_token']
    return IAM_TOKEN


def count_symbols(text):
    return len(text)


def text_to_speech(message):
    token = check_token()
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        'text': message,
        'lang': LANG,
        'voice': VOICE,
        'emotion': EMOTION,
        'speed': SPEED,
        'folderId': FOLDER_ID,
    }
    url = URL

    response = requests.post(url=url, headers=headers, data=data)
    if response.status_code == http.HTTPStatus.OK:
        return True, response.content
    else:
        logging.error('Что-то пошло не так при запросе к tts')
        return False, 'Что-то пошло не так'
