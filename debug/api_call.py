import requests

def call_refresh_config():
    headers = {
        'token': "bebebad3ddb9d50d433e487a8bf3ae48"
    }
    response = requests.post(f"https://ageverifier.roleplaymeets.com/config/refresh", headers=headers)
    return response.status_code

    if response.status_code == 200:
        return response.json()
    else:
        return response.raise_for_status()

print(call_refresh_config())