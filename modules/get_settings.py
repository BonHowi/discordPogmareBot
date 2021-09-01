import json
from functools import lru_cache

template_json = {
    "token": "None",
    "git_token": "None",
    "guild": 881161915689209936,
    "MOD_ROLES": "None",
    "CH_ROLE_REQUEST": "None",
    "CH_TOTAL_MEMBERS": "None",
    "CH_NIGHTMARE_KILL": "None",
    "CH_LEADERBOARDS": "None",
    "CH_TEMP": "None",
    "CH_COMMON": "None",
    "CH_LOGS": "None",
    "CH_VOICE_CHAT": "None",
    "CAT_SPOTTING": "None",
    "CH_COMMON_SPOTTING": "None"
}


@lru_cache()
def get_settings(key: str):
    """Get the selected key from the settings file"""
    try:
        with open("json_files/bot_settings.json", "r", encoding="UTF-8") as f:
            _json = json.load(f)
        return _json[key]
    except FileNotFoundError:
        with open("json_files/bot_settings.json", "w", encoding="UTF-8") as f:

            json.dump(template_json, f, indent=2)
        print("No bot_settings.json found. One has been created, please populate it and restart")
        exit(1)
    except KeyError:
        print(f"Incomplete bot_settings.json found,")
        print("Adding missing keys to bot_settings.json...")
        with open("json_files/bot_settings.json", "r+", encoding="UTF-8") as f:
            _json = json.load(f)
            for key in template_json.keys():
                if key not in _json.keys():
                    _json[key] = template_json[key]
                    print(f"Added {key}")
            f.truncate(0)
            f.seek(0)
            json.dump(_json, f, indent=2)
        exit(1)

# def sanity_check():
#     """Sanity checks the bot settings file to ensure smooth operation
#     Note: These are sanity checks, they only check that the file is "sane" nothing more"""
#     print(f"Sanity checking bot_settings.json\n{''.center(33, '=')}")
#     failed = False
#     for key in f.keys():
#         data = get_settings(key)
#         if data is None or data in ["Put Bot Token Here", "Put Git Token Here"]:
#             failed = True
#             print(f"{key} has not been set to a value")
#     if failed:
#         exit(1)
#     print("Sanity checks passed\n\n")
