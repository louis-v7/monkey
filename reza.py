import requests
import os
import datetime
import time

API_URL = 'https://api.resa.now/api/graphql/'
TARGET_DAYS = [0, 1, 2, 3]  # Lundi à Jeudi

def authenticate(email, password):
    headers_auth = {
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0',
    }

    data_auth = {
        "operationName": "Signin",
        "variables": {
            "login": email,
            "password": password
        },
        "query": """
        mutation Signin($login: String!, $password: String!) {
          Signin(login: $login, password: $password) {
            token
          }
        }
        """
    }

    response_auth = requests.post(API_URL, headers=headers_auth, json=data_auth)
    if response_auth.status_code == 200:
        result_auth = response_auth.json()
        if 'errors' in result_auth:
            print(f'Erreur pour {email} :', result_auth['errors'])
            return None
        else:
            token = result_auth['data']['Signin']['token']
            print(f'Token obtenu pour {email}')
            return token
    else:
        print(f'Erreur HTTP pour {email} :', response_auth.status_code)
        return None

def is_target_day(date):
    return date.weekday() in TARGET_DAYS

def calculate_uid(date):
    session_time = '19:30_20:30_planning_58_5'
    return f"{date.strftime('%Y-%m-%d')}_{session_time}"

def register_session(token, v_uid):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0',
    }

    data = {
        "operationName": "RegisterSession",
        "variables": {
            "uid": v_uid
        },
        "query": """
        mutation RegisterSession($uid: String!) {
          RegisterSession(uid: $uid) {
            uid
            Registration {
              status
            }
          }
        }
        """
    }

    for attempt in range(10):
        print(f"Tentative {attempt+1} pour s'inscrire à {v_uid}")
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if 'errors' in result:
                print('Erreur lors de l\'inscription :', result['errors'])
                time.sleep(60)
            else:
                print('Inscription réussie.')
                return result
        else:
            print('Erreur HTTP inscription :', response.status_code)
            time.sleep(60)
    return None

def send_discord_notification(response_json, email):
    discord_webhook_url = os.environ.get('DISCORD')
    registration = response_json['data']['RegisterSession']['Registration']
    if registration and registration['status'] == 'validated':
        uid = response_json['data']['RegisterSession']['uid']
        date_session, heure_debut, heure_fin, *_ = uid.split('_')
        message = f"✅ Réservation confirmée pour {email} : {date_session} de {heure_debut} à {heure_fin}."

        if discord_webhook_url:
            discord_data = {"content": message}
            r = requests.post(discord_webhook_url, json=discord_data)
            if r.status_code == 204:
                print(f'Notification Discord envoyée pour {email}.')
            else:
                print(f'Erreur Discord ({r.status_code}) pour {email}')
        else:
            print('Webhook Discord non défini.')
    else:
        print(f'Réservation non validée pour {email}.')

def process_account(email, password, uid):
    token = authenticate(email, password)
    if token:
        result = register_session(token, uid)
        if result:
            send_discord_notification(result, email)
        else:
            print(f'Échec d\'inscription pour {email}.')
    else:
        print(f'Échec d\'authentification pour {email}.')

def main():
    today = datetime.date.today()
    target_date = today + datetime.timedelta(days=7)

    if is_target_day(target_date):
        uid = calculate_uid(target_date)

        # Traitement du premier compte
        email1 = os.environ.get('MAIL')
        pwd1 = os.environ.get('MDP')
        process_account(email1, pwd1, uid)

        # Traitement du second compte
        email2 = os.environ.get('MAILE')
        pwd2 = os.environ.get('MDPE')
        process_account(email2, pwd2, uid)

    else:
        print(f"La date {target_date} n'est pas un jour cible. Aucune réservation faite.")

if __name__ == "__main__":
    main()
