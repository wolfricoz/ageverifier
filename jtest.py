import json
import os
from abc import ABC, abstractmethod
name = "Rico"
# Data to be written
class configer(ABC):
    @abstractmethod
    async def create(guildid, guildname):
        "Creates the config"
        dictionary = {
            "Name": guildname,
            "addrole": [],
            "remrole": [],
            "welcome": "",
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
            return data[key]
    async def remrole(guildid, roleid, key):
        if os.path.exists(f"jsons/{guildid}.json"):
            with open(f"jsons/{guildid}.json") as f:
                data = json.load(f)
                data[key].remove(roleid)
            with open(f"jsons/{guildid}.json", 'w') as f:
                json.dump(data, f, indent=4)
            return data[key]

