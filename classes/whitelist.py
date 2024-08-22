import json
import os

whitelist_path = 'whitelist.json'

def create_whitelist(guilds):
    """Creates a whitelist of guilds that the bot"""
    if os.path.exists(whitelist_path):
        return
    whitelist_date = {
        "whitelist": []
    }
    for guild in guilds:
        whitelist_date["whitelist"].append(guild.id)
    with open(whitelist_path, 'w') as f:
        json.dump(whitelist_date, f)


def check_whitelist(id):
    """Checks if the guild is in the whitelist"""
    with open(whitelist_path, 'r') as f:
        whitelist = json.load(f)
    if id in whitelist["whitelist"]:
        return True
    else:
        return False

def add_to_whitelist(id):
    """Adds a guild to the whitelist"""
    with open('whitelist.json', 'r') as f:
        whitelist = json.load(f)
    whitelist["whitelist"].append(id)
    with open(whitelist_path, 'w') as f:
        json.dump(whitelist, f)

def remove_from_whitelist(id):
    """Removes a guild from the whitelist"""
    with open('whitelist.json', 'r') as f:
        whitelist = json.load(f)
    whitelist["whitelist"].remove(id)
    with open(whitelist_path, 'w') as f:
        json.dump(whitelist, f)
