
* https://tesla-api.timdorr.com/
* https://www.teslaapi.io/vehicles/commands

## Usage:

``` 
  tesla.py [-h] [-l LIMIT] [-v] [-r] [-w] [-d] [-c {start,stop}]

Send commands to tesla.

optional arguments:
  -h, --help            show this help message and exit
  -l LIMIT, --set-charge-limit LIMIT
                        Percentage of the battery to set the charge to
  -v, --verbose         Verbose mode (priont json responses)
  -r, --revoke          Revoke saved token (logout) and exit
  -w, --wakeuip         Wake up vehicle
  -d, --dump            Dump the full config into json
  -c {start,stop}, --charge {start,stop}
                        Start or stop charge
```

## Possible use-cases:
- set target charge level according to a schedule
- stop charging at a desired time
- start charging at a desired time with granularity higher than 30 minutes
- periodically dump vehicle config to track changes

