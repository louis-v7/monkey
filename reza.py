import requests
from google.colab import userdata


# URL de l'API GraphQL
url = 'https://api.monkey-resa.com/graphql/'

# En-têtes de la requête initiale (authentification)
headers_auth = {
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'User-Agent': 'Mozilla/5.0',
}

# Étape 1 : Authentification
login = userdata.get('mail')    # Secrets dans userdate de google.colab
password = userdata.get('mdp')    # Secrets dans userdate de google.colab

data_auth = {
    "operationName": "Signin",
    "variables": {
        "login": login,
        "password": password
    },
    "query": """
    mutation Signin($login: String!, $password: String!) {
      Signin(login: $login, password: $password) {
        token
        token_ttl
        refresh_token
        firstname
        lastname
        picture
        lang
        theme
        has_workspace
        Clubs {
          id
          slug
          name
          __typename
        }
        __typename
      }
    }
    """
}

# Effectuer la requête d'authentification
response_auth = requests.post(url, headers=headers_auth, json=data_auth)

# Vérifier la réponse
if response_auth.status_code == 200:
    result_auth = response_auth.json()
    if 'errors' in result_auth:
        print('Erreur lors de la connexion :', result_auth['errors'])
    else:
        # Extraire le token de la réponse
        token = result_auth['data']['Signin']['token']
        print('Token obtenu :', token)



# prompt: a date in a yyyy_mm__dd format calculate today + 7 day

import datetime

def calculate_date_plus_7_days():
  today = datetime.date.today()
  seven_days_later = today + datetime.timedelta(days=7)
  return seven_days_later.strftime('%Y-%m-%d')


def calculate_uid():
  future_date = calculate_date_plus_7_days()
  session = future_date + '_07:00_08:00_planning_45_5'
  return session

v_uid = calculate_uid()



url = 'https://api.monkey-resa.com/graphql/'

headers = {
    'Authorization': f'Bearer {token}', #f-strings
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.120 Safari/537.36',
    'Sec-Ch-Ua': '"Not;A=Brand";v="24", "Chromium";v="128"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Accept-Language': 'fr-FR,fr;q=0.9',
    'Origin': 'https://monkey-resa.com',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://monkey-resa.com/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

data = {
    "operationName": "RegisterSession",
    "variables": {
        "uid": f"{v_uid}" #f-strings
    },
    "query": """mutation RegisterSession($uid: String!) {
  RegisterSession(uid: $uid) {
    uid
    max_registrations
    counter_registrations
    counter_pending
    Registration {
      status
      __typename
    }
    Registrations {
      firstname
      lastname
      status
      __typename
    }
    __typename
  }
}
"""
}

response = requests.post(url, headers=headers, json=data)

print(response.status_code)
print(response.text)
