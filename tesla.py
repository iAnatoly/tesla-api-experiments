from requests import post, get
from requests.utils import default_headers
from getpass import getpass
from json import dumps  # https://docs.python.org/2/library/json.html
from argparse import ArgumentParser # https://docs.python.org/3.3/library/argparse.html

class Config:
    default_email = 'anatoly.ivanov@gmail.com'

    def __init__(self):
        parser = ArgumentParser(description='Send commands to tesla.')
        parser.add_argument('-c', '--set-charge-limit', dest='limit', type=int, default=0, help='Percentage of the battery to set the charge to')
        parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, help='Verbose mode (priont json responses)')
        parser.add_argument('-r', '--revoke', dest='revoke', action='store_true', default=False, help='Revoke saved token and exit')
        
        args = parser.parse_args()
        
        self.limit = args.limit
        self.debug = args.verbose
        self.revoke = args.revoke

    def get_credentials(self):
        self.login = input('Enter your tesla.com login: [default={}]: '.format(Config.default_email))
        if not self.login: 
            self.login = Config.default_email
        else:
            self.login = self.login.strip()

        self.password = getpass('Please eneter password for {}: '.format(self.login))

class Tesla:
    ## API config
    client_id="81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384"
    client_secret="c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3"
    root = 'https://owner-api.teslamotors.com/api/1/{}'    
    oauth_token = 'https://owner-api.teslamotors.com/oauth/token'
    oauth_revoke = 'https://owner-api.teslamotors.com/oauth/revoke'


    def __init__(self, config: Config):
        ''' authenticate and save access token'''
        self.config = config
        self.load_token()
        
        if not self.is_token_valid():
            self.get_token()
            self.save_token()


    def __del__(self):
        ''' revoke access token to avoid pollution'''
        if self.token:
            response = post(Tesla.oauth_revoke, data='token={}'.format(self.token))
            print('Token {} revoked with status code {}.'.format(self.token[:5], response.status_code))

    def is_token_valid(self):
        return False

    def load_token(self):
        self.token = None 

    def save_token(self):
        pass

    def get_token(self):
        self.config.get_credentials()

        response = post(Tesla.oauth_token, data = {
            'client_id': Tesla.client_id,
            'client_secret': Tesla.client_secret,
            'grant_type': 'password',
            'email': self.config.login,
            'password': self.config.password,
            })

        if (self.config.debug): print('Received {} {} response.'.format(response.status_code, response.reason))
        if response.status_code == 401:
            print("Invalid credentials, please try again")
            exit(1)
     
        if response.status_code > 299: 
            raise Exception('Invalid response')

        payload = response.json()
        self.token = payload['access_token']

        print('Received token: ...{}.'.format(self.token[:5]))

    def get_json(self,method: str):
        ''' execute an authenticated GET request against a given method'''
        headers = default_headers()
        headers.update({'Authorization': 'bearer {}'.format(self.token)}) 
    
        response = get(self.root.format(method),headers=headers)
        json = response.json()

        if (self.config.debug): print(dumps(json, sort_keys=True, indent=4, separators=(',', ': ')))
    
        return json
    
    def post_json(self,method:str,json_data: dict):
        ''' execute an authenticated POST request against a given method, post provided data'''
        headers = default_headers()
        headers.update({'Authorization': 'bearer {}'.format(self.token)}) 
    
        response = post(self.root.format(method),data=json_data,headers=headers)
        json = response.json()
        if (self.config.debug): print(dumps(json, sort_keys=True, indent=4, separators=(',', ': ')))
        if response.status_code > 299: 
            raise Exception('Invalid response')

        return json

def print_stats(data: dict):
    firmware_version = data['response']['vehicle_state']['car_version']
    print('Firmware version: {}'.format(firmware_version))

    charge = data['response']['charge_state']

    battery_range = charge['battery_range']
    battery_level = charge['battery_level']
    
    print('Range: {} Battery: {}% Theoretical max range: {}'.format(
        battery_range, 
        battery_level, 
        battery_range*100//battery_level)
        )
    
    wh_added = charge['charge_energy_added']
    mi_added = charge['charge_miles_added_ideal']
    
    print('Charge started at {}'.format(battery_range-mi_added))

    charge_limit = charge['charge_limit_soc']
    print('Charge limit: {}'.format(charge_limit))

    rate = 0.24 # let us use supercharger rate as a baseline

    print('Engergy added: {}kwh ({} miles). That would be ${} at {} per kwh'.format(wh_added, mi_added, wh_added*rate, rate))
            
        
def main():
    config = Config()
    tesla = Tesla(config)

    vehicle_id = tesla.get_json('/vehicles')['response'][0]['id']    
    print('Working with vehicle_id={}'.format(vehicle_id))

    data = tesla.get_json('/vehicles/{}/data'.format(vehicle_id))
    print_stats(data)

    if config.limit>0:
        print('Updating the limit: {}->{}'.format(data['response']['charge_state']['charge_limit_soc'],config.limit))
        tesla.post_json('/vehicles/{}/command/set_charge_limit'.format(vehicle_id), json_data={ 'percent': config.limit })
           

main()
