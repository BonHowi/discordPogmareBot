import json
from functools import lru_cache

template_json = {
    "token": "None",
    "git_token": "None",
    "guild": [881161915689209936],
    "ADMIN": "None",
    "MOD_ROLES": [],
    "CH_ADMIN_POSTING": "None",
    "CH_ROLE_REQUEST": "None",
    "CH_TOTAL_MEMBERS": "None",
    "CH_NIGHTMARE_KILLED": "None",
    "CH_LEADERBOARDS": "None",
    "CH_TEMP": "None",
    "CH_COMMON": "None",
    "CH_LOGS": "None",
    "CH_VOICE_CHAT": "None",
    "CH_DISCUSSION_EN": "None",
    "CAT_SPOTTING": "None",
    "EXCEL_ID": "None",
    "DB_P": "None"
}


@lru_cache()
def get_settings(key: str):
    """Get the selected key from the settings file"""
    try:
        with open("server_files/bot_settings.json", "r", encoding="UTF-8") as f:
            _json = json.load(f)
        return _json[key]
    except FileNotFoundError:
        with open("server_files/bot_settings.json", "w", encoding="UTF-8") as f:
            json.dump(template_json, f, indent=2)
        print("No bot_settings.json found. One has been created, please populate it and restart")
        exit(1)
    except KeyError:
        print(f"Incomplete bot_settings.json found\n"
              f"Check your file")
        exit(1)
