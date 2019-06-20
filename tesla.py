#!/usr/bin/env python3
from requests import post, get
from requests.exceptions import ConnectionError
from requests.utils import default_headers
from getpass import getpass
from time import sleep
from json import dumps, dump, load  # https://docs.python.org/2/library/json.html
from argparse import ArgumentParser # https://docs.python.org/3.3/library/argparse.html
from os.path import expanduser

# Tesla API reference:
# * https://tesla-api.timdorr.com/
# * https://www.teslaapi.io/vehicles/commands

class InvalidCredentialsException(Exception):
    pass

class VehicleAsleepException(Exception):
    pass

class UnexpectedResponseException (Exception):
    pass

class Config:
    default_email = 'anatoly.ivanov@gmail.com'

    def __init__(self):
        parser = ArgumentParser(description='Send commands to tesla.')
        parser.add_argument('-c', '--set-charge-limit', dest='limit', type=int, default=0, help='Percentage of the battery to set the charge to')
        parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, help='Verbose mode (priont json responses)')
        parser.add_argument('-r', '--revoke', dest='revoke', action='store_true', default=False, help='Revoke saved token (logout) and exit')
        parser.add_argument('-w', '--wakeuip', dest='wakeup', action='store_true', default=False, help='Wake up vehicle')
        parser.add_argument('-d', '--dont', dest='cancel_update', action='store_true', default=False, help='Cancel the software update')
        
        args = parser.parse_args()
        
        self.limit = args.limit
        self.debug = args.verbose
        self.revoke = args.revoke
        self.wakeup = args.wakeup
        self.cancel_update = args.cancel_update
        self.rate = 0.13 # let us use PGE EV rate as baseline


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
    token_file = expanduser("~")+'/.tesla_token'


    def __init__(self, config: Config):
        ''' authenticate and save access token'''
        self.config = config
        self.load_token()

        if config.revoke:
            self.revoke_token()
            exit(2)
        
        if not self.is_token_valid():
            self.get_token()
            self.save_token()


    def __del__(self):
        pass

    def revoke_token(self):
        ''' revoke access token to avoid pollution'''
        if self.token:
            response = post(Tesla.oauth_revoke, data='token={}'.format(self.token))
            print('[!] Token {} revoked with status code {}.'.format(self.token[:5], response.status_code))

    def is_token_valid(self):
        return self.token is not None

    def load_token(self):
        try:
            with open(Tesla.token_file, 'r') as f:
                token_json = load(f)
                self.token = token_json['token']
        except:
            self.token = None 

    def save_token(self):
        with open(Tesla.token_file, 'w+') as f:
            dump({ 'token': self.token }, f)

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
            raise InvalidCredentialsException()
     
        if response.status_code > 299: 
            raise Exception('Invalid response: {} {}'.format(response.status_code, response.reason))

        payload = response.json()
        self.token = payload['access_token']

        print('[!] Received token: ...{}.'.format(self.token[:5]))

    def get_json(self,method: str):
        ''' execute an authenticated GET request against a given method'''
        headers = default_headers()
        headers.update({'Authorization': 'bearer {}'.format(self.token)}) 
    
        response = get(self.root.format(method),headers=headers)
        if self.config.debug: print(response.status_code, response.reason)
        
        if response.status_code == 408:
            raise VehicleAsleepException()
     
        if response.status_code > 299: 
            raise UnexpectedResponseException('Invalid response: {} {}'.format(response.status_code, response.reason))


        json = response.json()

        if (self.config.debug): print(dumps(json, sort_keys=True, indent=4, separators=(',', ': ')))
    
        return json
    
    def post_json(self,method:str,json_data: dict = None):
        ''' execute an authenticated POST request against a given method, post provided data'''
        headers = default_headers()
        headers.update({'Authorization': 'bearer {}'.format(self.token)}) 
    
        response = post(self.root.format(method),data=json_data,headers=headers)
        json = response.json()
        if (self.config.debug): print(dumps(json, sort_keys=True, indent=4, separators=(',', ': ')))
        
        if response.status_code == 408:
            raise VehicleAsleepException()
     
        if response.status_code > 299: 
            raise Exception('Invalid response: {} {}'.format(response.status_code, response.reason))

        if 'response' in json:
            if 'result' in json['response']:
                print('[*] Result: {}; reason: {}'.format(json['response']['result'], json['response']['reason']))

        return json

def print_stats(data: dict, rate):
    firmware_version = data['response']['vehicle_state']['car_version']
    print('    Current firmware version: {}'.format(firmware_version))
    
    update = data['response']['vehicle_state']['software_update']
    duration = update['expected_duration_sec']
    status = update['status']
    if status:
        print('[!] Software update: {}; Expected installation duration: {}'.format(status, duration))

    charge = data['response']['charge_state']

    battery_range = charge['battery_range']
    battery_level = charge['battery_level']
    
    print('    Range: {} Battery: {}% Theoretical max range: {}'.format(
        battery_range, 
        battery_level, 
        battery_range*100//battery_level)
        )
        
    charge_limit = charge['charge_limit_soc']
    charge_state = charge['charging_state']

    print('    Charge limit: {}%'.format(charge_limit))

    if charge_state == 'Charging' or charge_state == 'Complete':
        charge_rate = charge['charge_rate']
    
        wh_added = charge['charge_energy_added']
        mi_added = charge['charge_miles_added_ideal']

        current = charge['charger_actual_current']
        voltage = charge['charger_voltage']

        # todo: charge_current_request and calc charge deficit
        # todo: compare voltage and calculate power loss in the conductor
    
        print('    Charge started at {} miles; current: {} Amp, voltage: {} Volts'.format(battery_range-mi_added, current, voltage))
        print('    Engergy added: {}kwh ({} miles). That would be ${} at {} per kwh'.format(wh_added, mi_added, wh_added*rate, rate))
            
        
def main():
    config = Config()
    tesla = Tesla(config)

    try:
        vehicle_id = tesla.get_json('/vehicles')['response'][0]['id']    
        print('\n[*] Working with vehicle_id={}'.format(vehicle_id))

        if config.wakeup:
            awake = False
            while not awake:
                try:
                    tesla.post_json('/vehicles/{}/wake_up'.format(vehicle_id))
                    awake = True
                except VehicleAsleepException:
                    print("...waking up...")
                    sleep(10)
                    
        data = tesla.get_json('/vehicles/{}/data'.format(vehicle_id))
        print_stats(data, config.rate)

        if config.limit>0:
            print('    Updating the limit: {}%->{}%'.format(data['response']['charge_state']['charge_limit_soc'],config.limit))
            tesla.post_json('/vehicles/{}/command/set_charge_limit'.format(vehicle_id), json_data={ 'percent': config.limit })

        if config.cancel_update:
            print('    Attempting to cancel the update')
            tesla.post_json('/vehicles/{}/command/cancel_software_update'.format(vehicle_id), json_data={})
            
    except InvalidCredentialsException as ex:
        print("[E] Invalid credentials: {}".format(ex.message))
    except VehicleAsleepException as ex:
        print("[!] Vehicle is asleep. Try walking it up with -w")
    except UnexpectedResponseException as ex:
        print("[E] Unexpected response: {}".format(ex.message))           
    except ConnectionError as err:
        print("[E] Connection error: {}".format(err))

main()
