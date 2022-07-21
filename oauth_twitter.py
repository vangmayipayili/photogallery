import os
from requests_oauthlib import OAuth1Session

# Request an OAuth Request Token. This is the first step of the 3-legged OAuth flow. This generates a token that you can use to request user authorization for access.

def request_token():
    oauth = OAuth1Session(os.environ["TWT_CONSUMER_KEY"], client_secret=os.environ["TWT_CONSUMER_SECRET"], callback_uri=os.environ["DOMAIN"]+"/oauth/twitter")

    url = "https://api.twitter.com/oauth/request_token"
    response = oauth.fetch_request_token(url)
    resource_owner_oauth_token = response.get('oauth_token')
    resource_owner_oauth_token_secret = response.get('oauth_token_secret')
    return resource_owner_oauth_token, resource_owner_oauth_token_secret

def get_user_authorization(resource_owner_oauth_token):

    authorization_url = f"https://api.twitter.com/oauth/authorize?oauth_token={resource_owner_oauth_token}"
    authorization_pin = input(f" \n Send the following URL to the user you want to generate access tokens for. \n → {authorization_url} \n This URL will allow the user to authorize your application and generate a PIN. \n Paste PIN here: ")

    return(authorization_pin)


# Exchange the OAuth Request Token you obtained previously for the user’s Access Tokens.
def get_user_access_tokens(resource_owner_oauth_token, resource_owner_oauth_token_secret, authorization_pin):
    oauth = OAuth1Session(os.environ["TWT_CONSUMER_KEY"],
                          client_secret=os.environ["TWT_CONSUMER_SECRET"],
                          resource_owner_key=resource_owner_oauth_token,
                          resource_owner_secret=resource_owner_oauth_token_secret,
                          verifier=authorization_pin)

    url = "https://api.twitter.com/oauth/access_token"

    response = oauth.fetch_access_token(url)
    access_token = response['oauth_token']
    access_token_secret = response['oauth_token_secret']
    user_id = response['user_id']
    screen_name = response['screen_name']

    return (access_token, access_token_secret, user_id, screen_name)