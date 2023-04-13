import os

import requests
from dotenv import load_dotenv
from fixieai import (CodeShotAgent, Message, OAuthHandler, OAuthParams,
                     UserStorage)

load_dotenv()

BASE_PROMPT = "I am an agent in charge of retrieving enterprise data or knowledge to be used as context for another agent. Tell me in natural language what enterprise data you're looking for and I will return it."
FEW_SHOTS = """
Q: My last 2 zendesk tickets.
Ask Func[qa]: What are my last 2 zendesk tickets?
Func[qa] says: Your first ticket involves an issue with the website. The second ticket is about a problem with the app.
A: My last 2 zendesk tickets are: Your first ticket involves an issue with the website. The second ticket is about a problem with the app.

Q: Deals closed with Morlong Associates.
Ask Func[qa]: What deals have I closed with Morlong Associates?
Func[qa] says: You closed 3 deals with Morlong Associates.
A: I closed 3 deals with Morlong Associates.
"""

oauth_params = OAuthParams(
    client_id=os.getenv('MIMO_CLIENT_ID'),
    auth_uri="https://dev-co2rq0sc2r5fv2gk.us.auth0.com/authorize",
    token_uri="https://dev-co2rq0sc2r5fv2gk.us.auth0.com/oauth/token",
    client_secret=os.getenv('MIMO_CLIENT_SECRET'),
    scopes=['openid', 'profile', 'email', 'offline_access']
)

agent = CodeShotAgent(BASE_PROMPT, FEW_SHOTS, oauth_params=oauth_params)

@agent.register_func
def qa(query: Message, oauth_handler: OAuthHandler, user_storage: UserStorage) -> str:
    user_token = None
    try:
        user_token = oauth_handler.user_token()
    except Exception as e:
        # TODO: generalize a bit more. currently only exceptions during refresh it looks like
        print(e)
        user_storage[OAuthHandler.OAUTH_TOKEN_KEY] = None

    if user_token is None:
        url = oauth_handler.get_authorization_url()
        return url + f'&audience=https%3A%2F%2Fapi.mimo.team%2F'
    
    print('hi??')
    response = requests.get(
        'https://ztsl6igv66ognn6qpvsfict6y40qocst.lambda-url.us-east-1.on.aws/',
        headers={
            'Authorization': f'Bearer {user_token}'
        },
        params={
            'question': query.text
        },
        timeout=300
    )
    print(response)
    qa_response = response.json()
    print(qa_response)
    return qa_response.get('answer', 'Sorry, I don\'t know.') if qa_response else 'Sorry, Mimo is unavailable.'
