# shell playground to experiment with the APIs
# Just paste auth token, then get vehicles, then paste vehicle ID...

AUTH="Authorization: Bearer ${TOKEN}"
ROOT="https://owner-api.teslamotors.com/"
TESLA_CLIENT_ID="81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384"
TESLA_CLIENT_SECRET="c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3"

# curl -H "Content-Type: application/json" "${ROOT}/oauth/token" --data "{  'grant_type': 'password',  'client_id': '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384',  'client_secret': 'c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3',  'email': '',  'password': '' } "
TOKEN=""

# curl -H "$AUTH" "${ROOT}/oauth/revoke" --data "token=${TOKEN}" | python -m json.tool
# curl -H "$AUTH" "${ROOT}/api/1/users/onboarding_data" | python -m json.tool

# curl -H "$AUTH" "${ROOT}/api/1/vehicles" | python -m json.tool
VEHICLE_ID="NNNNNNN"

# curl -H "$AUTH" "${ROOT}/api/1/vehicles/${VEHICLE_ID}/data" | python -m json.tool
# curl -H "$AUTH" "${ROOT}/api/1/vehicles/${VEHICLE_ID}/data_request/vehicle_state" | python -m json.tool
# curl -H "$AUTH" "${ROOT}/api/1/vehicles/${VEHICLE_ID}/data_request/charge_state" | python -m json.tool
#curl -H "$AUTH" "${ROOT}/api/1/vehicles/${VEHICLE_ID}/data_request/vehicle_config" | python -m json.tool
#curl -H "$AUTH" "${ROOT}/api/1/vehicles/${VEHICLE_ID}/data_request/gui_settings" | python -m json.tool
#curl -H "$AUTH" "${ROOT}/api/1/vehicles/${VEHICLE_ID}/command/schedule_software_update" --data "{'offset_sec':'0'}" | python -m json.tool
# curl -H "$AUTH" "${ROOT}/api/1/vehicles/${VEHICLE_ID}/command/charge_standard" -XPOST | python -m json.tool
