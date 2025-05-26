import requests
import os
import datetime
import time

# URL de l'API GraphQL
API_URL = 'https://api.resa.now/api/graphql/'

# Jours cibles pour la réservation (0: Lundi, 2: Mercredi, 3: Jeudi)
TARGET_DAYS = [0, 1, 2, 3]

def authenticate():
    """Authentifie l'utilisateur et retourne le token."""
    # En-têtes de la requête d'authentification
    headers_auth = {
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0',
    }
    # Informations d'identification
    login = os.environ.get('MAIL')
    password = os.environ.get('MDP')

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
    response_auth = requests.post(API_URL, headers=headers_auth, json=data_auth)
    if response_auth.status_code == 200:
        result_auth = response_auth.json()
        if 'errors' in result_auth:
            print('Erreur lors de la connexion :', result_auth['errors'])
            return None
        else:
            token = result_auth['data']['Signin']['token']
            print('Token obtenu :', token)
            return token
    else:
        print('Erreur lors de la requête d\'authentification :', response_auth.status_code)
        print('Message :', response_auth.text)
        return None

def is_target_day(date):
    """Vérifie si la date est un jour cible."""
    weekday = date.weekday()  # 0: Lundi, ..., 6: Dimanche
    return weekday in TARGET_DAYS

def calculate_uid(date):
    """Construit l'UID de la session à partir de la date."""
    session_time = '19:30_20:30_planning_58_5'  # Ajustez si nécessaire
    uid = f"{date.strftime('%Y-%m-%d')}_{session_time}"
    return uid

def register_session(token, v_uid):
    """Tente de s'inscrire à la session avec des tentatives multiples."""
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

    max_attempts = 10
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        print(f'Tentative {attempt} pour s\'inscrire à la session {v_uid}')
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if 'errors' in result:
                print('Erreur lors de l\'inscription :', result['errors'])
                time.sleep(60)  # Attendre 1 minute avant de réessayer
            else:
                print('Inscription réussie.')
                return result
        else:
            print('Erreur lors de la requête :', response.status_code)
            print('Message :', response.text)
            time.sleep(60)  # Attendre 1 minute avant de réessayer
    print('Toutes les tentatives ont échoué.')
    return None

def send_discord_notification(response_json):
    """Envoie une notification au webhook Discord si la réservation est validée."""
    discord_webhook_url = os.environ.get('DISCORD')
    registration = response_json['data']['RegisterSession']['Registration']
    if registration and registration['status'] == 'validated':
        uid = response_json['data']['RegisterSession']['uid']
        date_session, heure_debut, heure_fin, *_ = uid.split('_')
        message = f"✅ Votre réservation pour la session du {date_session} de {heure_debut} à {heure_fin} a été validée."

        if discord_webhook_url:
            discord_data = {
                "content": message
            }
            discord_response = requests.post(discord_webhook_url, json=discord_data)
            if discord_response.status_code == 204:
                print('Message envoyé avec succès au webhook Discord.')
            else:
                print('Erreur lors de l\'envoi du message au webhook Discord :', discord_response.status_code)
        else:
            print('Erreur : l\'URL du webhook Discord n\'est pas définie.')
    else:
        print('La réservation n\'a pas été validée.')

def main():
    token = authenticate()
    if not token:
        print('Échec de l\'authentification.')
        return

    # Calculer la date dans 7 jours
    today = datetime.date.today()
    future_date = today + datetime.timedelta(days=7)

    # Vérifier si la date est un jour cible
    if is_target_day(future_date):
        v_uid = calculate_uid(future_date)
        result = register_session(token, v_uid)
        if result:
            send_discord_notification(result)
        else:
            print('Échec de l\'inscription après plusieurs tentatives.')
    else:
        print(f'La date {future_date} n\'est pas un jour cible. Aucune action effectuée.')

if __name__ == "__main__":
    main()
