import requests
import json


def get_ids(names):
    return requests.post(
        "https://esi.evetech.net/latest/universe/ids/?datasource=tranquility&language=en",
        data=json.dumps(names),
        headers={
            'Accept': 'application/json',
            'Accept-Language': 'en',
            'Content-Type': 'application/json',
            'User-Agent': 'Contact Calir Deminar'
        }
    ).json()


def get_names(ids):
    return requests.post(
        "https://esi.evetech.net/latest/universe/names/?datasource=tranquility&language=en",
        data=json.dumps(ids),
        headers={
            'Accept': 'application/json',
            'Accept-Language': 'en',
            'Content-Type': 'application/json',
            'User-Agent': 'Contact Calir Deminar'
        }
    ).json()


def get_raw_corp_history(character_id):
    char_id = str(character_id).replace("\n", "")
    headers = requests.utils.default_headers()
    headers.update({'User-Agent': 'Contact Calir Deminar'})
    url = ("https://esi.evetech.net/latest/characters/" +
           char_id +
           "/corporationhistory/?datasource=tranquility")
    resp = list(requests.get(url, headers=headers).json())
    return resp
