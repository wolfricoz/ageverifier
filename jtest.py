import json
import os
from abc import ABC, abstractmethod
# Data to be written
class configer(ABC):
    @abstractmethod
    async def create(guildid, guildname):
        "Creates the config"
        dictionary = {
            "Name": guildname,
            "addrole": [],
            "remrole": [],
            "welcomeusers": True,
            "welcome": "This can be changed with /config welcome",
            "waitingrole": [],
        }
        json_object = json.dumps(dictionary, indent=4)
        if os.path.exists(f"jsons/{guildid}.json"):
            print(f"{guildid} already has a config")
            with open(f"jsons/template.json", "w") as outfile:
                outfile.write(json_object)
        else:
            with open(f"jsons/{guildid}.json", "w") as outfile:
                outfile.write(json_object)
                print(f"config created for {guildid}")
    @abstractmethod
    async def addrole(guildid, interaction, roleid, key):
        if os.path.exists(f"jsons/{guildid}.json"):
            with open(f"jsons/{guildid}.json") as f:
                data = json.load(f)
                for x in data[key]:
                    if x == roleid:
                        await interaction.followup.send("Failed to add role! Role already in config")
                        break
                else:
                    data[key].append(roleid)
                    await interaction.followup.send(f"Role added to {key}")
            with open(f"jsons/{guildid}.json", 'w') as f:
                json.dump(data, f, indent=4)
    @abstractmethod
    async def remrole(guildid, roleid, key):
        if os.path.exists(f"jsons/{guildid}.json"):
            with open(f"jsons/{guildid}.json") as f:
                data = json.load(f)
                data[key].remove(roleid)
            with open(f"jsons/{guildid}.json", 'w') as f:
                json.dump(data, f, indent=4)
    @abstractmethod
    async def welcome(guildid, interaction,key, welcome):
        if os.path.exists(f"jsons/{guildid}.json"):
            with open(f"jsons/{guildid}.json") as f:
                data = json.load(f)
                data[key] = welcome
            with open(f"jsons/{guildid}.json", 'w') as f:
                json.dump(data, f, indent=4)
            await interaction.followup.send(f"welcome updated to '{welcome}'")
    @abstractmethod
    async def updateconfig(guildid):
        with open(f'jsons/{guildid}.json', 'r+') as file:
            data = json.load(file)
            newdictionary = {
                "Name": data.get('Name', None),
                "addrole": data.get('addrole', []),
                "remrole": data.get('remrole', []),
                "welcomeusers": data.get("welcomeusers", False),
                "welcome": data.get('welcome', "This can be changed with /config welcome"),
                "waitingrole": data.get('waitingrole', []),
                "delete": data.get('delete', False)
            }

        with open(f'jsons/{guildid}.json', 'w') as f:
            json.dump(newdictionary, f, indent=4)

    @abstractmethod
    def read(guildid, key):
        with open(f'jsons/{guildid}.json', 'r+') as file:
            data = json.load(file)
            value = data[key]
        return value
    @abstractmethod
    def trueorfalse(guildid, key, value: bool):
        with open(f'jsons/{guildid}.json', 'r+') as file:
            data = json.load(file)
            data[key] = value
        with open(f'jsons/{guildid}.json', 'w') as file:
            json.dump(data, file, indent=4)


    @abstractmethod
    async def viewconfig(interaction, guildid):
        if os.path.exists(f"jsons/{guildid}.json"):
            with open(f"jsons/{guildid}.json") as f:
                data = json.load(f)
                vdict = f"""
Name: {data['Name']}
addrole: {data['addrole']}
remrole: {data['remrole']}
welcomeusers: {data['welcomeusers']},
welcome: {data['welcome']}
waitingrole: {data['waitingrole']}
                """
                return vdict




