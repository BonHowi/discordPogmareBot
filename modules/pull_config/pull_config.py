import json
import os.path

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from numpyencoder import NumpyEncoder

# from main import MyBot
from modules import get_settings

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SAMPLE_RANGE_NAME = 'A1:AA200'

SAMPLE_SPREADSHEET_ID_input = get_settings.get_settings("EXCEL_ID")


def handle_creds(creds, token: str) -> None:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'pull_config/credentials/client_secret.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(token, 'w') as token:
        token.write(creds.to_json())


def import_from_sheets():
    token: str = "token.json"
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists(token):
        creds = Credentials.from_authorized_user_file(token, SCOPES)
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        handle_creds(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result_input = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID_input, range=SAMPLE_RANGE_NAME).execute()
    values_input = result_input.get('values', [])

    # if not values_input:
    #     dt_string = MyBot.get_current_time()
    #     print(f"({dt_string})\t[{get_config.__name__}]: No data found.")
    return values_input


def create_trigger_list(triggers) -> list:
    triggers_list = []
    for row in triggers.itertuples(index=False):
        help_ser = pd.Series(row)
        help_ser = help_ser[~help_ser.isna()]
        # Drop empty strings
        help_ser = pd.Series(filter(None, help_ser))
        # Copy strings with spaces without keeping them
        for trigger in help_ser:
            trigger_nospace = trigger.replace(' ', '')
            help_ser = help_ser.append(pd.Series(trigger_nospace))
        help_ser = help_ser.drop_duplicates()
        triggers_list.append(help_ser)
    return triggers_list


def create_output(monsters_df: pd.DataFrame) -> dict:
    types = {'id': [4, 3, 2, 1, 0], 'label': ["Common", "Event2", "Event1", "Legendary", "Rare"]}
    types_df = pd.DataFrame(data=types)
    total_milestones = {"Sunday Spotter I": [100], "Sunday Spotter II": [200], "Sunday Spotter III": [300],
                        "Rare Spotter I": [500], "Rare Spotter II": [750], "Rare Spotter III": [1000],
                        "Pro Spotter I": [1500], "Pro Spotter II": [2000], "Pro Spotter III": [2500],
                        "Legendary Spotter I": [3500], "Legendary Spotter II": [4500], "Legendary Spotter III": [5500],
                        "Mythic Spotter I": [7500], "Mythic Spotter II": [9500], "Mythic Spotter III": [11500],
                        "Pogmare Spotter": [15000]}
    total_milestones_df = pd.DataFrame(data=total_milestones)
    common_milestones = {"Common Spotter": [100], "Common Killer": [500], "Common Slayer": [1000],
                         "Common Destroyer": [1500], "Common Annihilator": [2500]}
    common_milestones_df = pd.DataFrame(data=common_milestones)
    json_final = {'total_milestones': total_milestones_df, 'common_milestones': common_milestones_df,
                  'types': types_df, 'commands': monsters_df}
    return {
        key: json_final[key].to_dict(orient='records')
        for key in json_final
    }


def create_trigger_structure(triggers_list: list) -> pd.Series:
    triggers_def = [list(i) for i in triggers_list]
    return pd.Series(triggers_def)


def get_config() -> None:
    pd.set_option('mode.chained_assignment', None)
    values_input = import_from_sheets()
    df = pd.DataFrame(values_input[1:], columns=values_input[0])

    monsters_df = df[["name", "type"]]
    monsters_df["type"] = pd.to_numeric(df["type"])

    triggers = df.drop(['name', 'role', 'type', 'id'], axis=1)
    triggers = triggers.applymap(lambda s: s.lower() if type(s) == str else s)

    triggers_list = create_trigger_list(triggers)

    triggers_def = create_trigger_structure(triggers_list)
    monsters_df.insert(loc=0, column='triggers', value=triggers_def)

    data_dict = create_output(monsters_df)

    # write to disk
    with open('server_files/config.json', 'w', encoding='utf8') as f:
        json.dump(data_dict, f, indent=4, ensure_ascii=False, sort_keys=False, cls=NumpyEncoder)


def main() -> None:
    get_config()


if __name__ == "__main__":
    main()
