import requests

IP = "http://127.0.0.1:8080"
def call_refresh_config() :
	headers = {
		'token' : "bebebad3ddb9d50d433e487a8bf3ae48"
	}
	response = requests.post(f" ", headers=headers)
	return response.status_code

	if response.status_code == 200 :
		return response.json()
	else :
		return response.raise_for_status()


def call_auto_config() :
	headers = {
		'token' : "bebebad3ddb9d50d433e487a8bf3ae48"
	}
	response = requests.post(f"{IP}/config/1048433044253573120/autosetup", headers=headers)

	if response.status_code == 200 :
		return response.json()
	else :
		return response.raise_for_status()

def call_permission_check() :
	headers = {
		'token' : "bebebad3ddb9d50d433e487a8bf3ae48"
	}
	response = requests.post(f"{IP}/config/1048433044253573120/permissioncheck", headers=headers)

	if response.status_code == 200 :
		return response.json()
	else :
		return response.raise_for_status()

# print(call_refresh_config())
# print(call_auto_config())
print(call_permission_check())