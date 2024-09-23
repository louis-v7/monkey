import requests
import os
import datetime

# URL de l'API GraphQL
url = 'https://api.monkey-resa.com/graphql/'

discord_webhook_url = os.environ.get('DISCORD')
print(discord_webhook_ur)

# En-têtes de la requête initiale (authentification)
headers_auth = {
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'User-Agent': 'Mozilla/5.0',
}

# Étape 1 : Authentification
login = os.environ.get('MAIL')       # Récupère le mail depuis les variables d'environnement
password = os.environ.get('MDP')     # Récupère le mot de passe depuis les variables d'environnement

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
else:
    print('Erreur lors de la requête d\'authentification :', response_auth.status_code)
    print('Message :', response_auth.text)
    exit(1)

# Calculer la date dans 7 jours au format yyyy-mm-dd
def calculate_date_plus_7_days():
    today = datetime.date.today()
    seven_days_later = today + datetime.timedelta(days=6)
    return seven_days_later.strftime('%Y-%m-%d')

# Construire l'UID
def calculate_uid():
    future_date = calculate_date_plus_7_days()
    session = future_date + '_19:30_20:30_planning_58_5'
    return session

v_uid = calculate_uid()
v_uid = '2024-09-27_19:30_20:30_planning_58_5'

# Fonction pour vérifier le statut et envoyer un message au webhook Discord
def send_discord_notification(response_json):
    # Vérifier si le statut est 'validated'
    registration = response_json['data']['RegisterSession']['Registration']
    if registration and registration['status'] == 'validated':
        # Préparer le message
        uid = response_json['data']['RegisterSession']['uid']
        date_session = uid.split('_')[0]
        heure_debut = uid.split('_')[1]
        heure_fin = uid.split('_')[2]
        message = f"✅ Votre réservation pour la session du {date_session} de {heure_debut} à {heure_fin} a été validée."

        # Envoyer le message à votre webhook Discord
        discord_webhook_url = os.environ.get('DISCORD')

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



# Préparer les en-têtes pour la requête avec le token
headers = {
    'Authorization': f'Bearer {token}',  # En-tête d'authentification avec le token Bearer
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'User-Agent': 'Mozilla/5.0',
}

# Préparer les données pour la mutation RegisterSession
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

# Effectuer la requête pour s'inscrire à la session
response = requests.post(url, headers=headers, json=data)

# Afficher le résultat
print('Code de statut de la réponse :', response.status_code)
print('Réponse :', response.text)

# Analyser la réponse JSON
if response.status_code == 200:
    result = response.json()
    if 'errors' in result:
        print('Erreur lors de l\'inscription :', result['errors'])
    else:
        # Appeler la fonction pour envoyer la notification
        send_discord_notification(result)
else:
    print('Erreur lors de la requête :', response.status_code)
