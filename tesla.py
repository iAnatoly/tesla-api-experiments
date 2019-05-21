from requests import post, get
from requests.utils import default_headers
from getpass import getpass
from json import dumps  # https://docs.python.org/2/library/json.html
    
class Tesla:
    ## config
    client_id="81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384"
    client_secret="c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3"
    root = 'https://owner-api.teslamotors.com/api/1/{}'    

    def __init__(self, username,password):
        ''' authenticate and save access token'''
        response = post('https://owner-api.teslamotors.com/oauth/token', data={
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'password',
            'email': username,
            'password': password,
            })

        print('Received {} {} response.'.format(response.status_code, response.reason))
        if response.status_code > 299: 
            raise Exception('Invalid response')

        payload = response.json()
        self.token = payload['access_token']
        print('Received token: ...{}.'.format(self.token[:5]))

    def __del__(self):
        ''' revoke access token to avoid pollution'''
        response = post('https://owner-api.teslamotors.com/oauth/revoke', data='token={}'.format(self.token))
        print('Token {} revoked with status code {}.'.format(self.token[:5], response.status_code))

    def get_json(self,method):
        ''' execute an authenticated GET request against a given method'''
        headers = default_headers()
        headers.update({'Authorization': 'bearer {}'.format(self.token)}) 
    
        response = get(self.root.format(method),headers=headers)
        json = response.json()
        print(dumps(json, sort_keys=True, indent=4, separators=(',', ': ')))
    
        return json
    
    def post_json(self,method,json_data):
        ''' execute an authenticated POST request against a given method, post provided data'''
        headers = default_headers()
        headers.update({'Authorization': 'bearer {}'.format(self.token)}) 
    
        response = post(self.root.format(method),data=json_data,headers=headers)
        json = response.json()
        print(dumps(json, sort_keys=True, indent=4, separators=(',', ': ')))
    
        return json

def get_credentials(default_email):
    login = input('Enter your tesla.com login: [default={}]: '.format(default_email))
    if not login: 
        login = default_email
    else:
        login = login.strip()

    password = getpass('Please eneter password for {}: '.format(login))
    return login,password

def main():

    (login,password) = get_credentials(default_email="anatoly.ivanov@gmail.com")

    tesla = Tesla(login, password)

    vehicle_id = tesla.get_json('/vehicles')['response'][0]['id']    
    print('Working with vehicle_id={}'.format(vehicle_id))

    data = tesla.get_json('/vehicles/{}/data'.format(vehicle_id))

main()
