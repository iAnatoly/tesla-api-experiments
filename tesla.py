from requests import post, get
from requests.utils import default_headers
from getpass import getpass
    

def get_token(username,password):
    ''' get an access token in exchange for login+password '''
    
    ## config
    client_id="81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384"
    client_secret="c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3"
    
    headers = default_headers()
    response = post('https://owner-api.teslamotors.com/oauth/token', data={
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'password',
        'email': username,
        'password': password,
        }, headers=headers)

    # DEBUG:
    print('Received {} {} response.'.format(response.status_code, response.reason))
    if response.status_code > 299: raise Exception('Invalid response')

    payload = response.json()
    token= payload['access_token']
    print('Received token: ...{}.'.format(token[:5]))
    return token

def revoke_token(token):
    response = post('https://owner-api.teslamotors.com/oauth/revoke', data='token={}'.format(token))
    print('Token {} revoked with status code {}.'.format(token[:5], response.status_code))


def main():
    
    email = "anatoly.ivanov@gmail.com" 
    login = input('Enter your tesla.com login: [default={}]: '.format(email))
    if not login: 
        login=email
    else:
        login=login.strip()

    password = getpass('Please eneter password for {} :'.format(login))
 
    token = get_token(login, password)
    
    revoke_token(token)


main()
