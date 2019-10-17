#!/bin/bash
STATE=`./tesla.py | grep "Charge state:" | cut -d ' ' -f 7`
if [ "x${STATE}" != "xCharging" ] ; then
    amixer -D pulse sset Master 100%
    espeak "ALARM! ALARM! Tesla Not Charging"
fi
