import pandas as pd
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json
from modules import get_settings

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SAMPLE_RANGE_NAME = 'A1:AA68'
CREDENTIALS_FILE = 'pull_config/credentials/client_secret.com.json '

SAMPLE_SPREADSHEET_ID_input = get_settings.get_settings("EXCEL_ID")


def import_from_sheets():
    """

    :return:
    :rtype:
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result_input = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID_input, range=SAMPLE_RANGE_NAME).execute()
    values_input = result_input.get('values', [])

    if not values_input:
        print('No data found.')
    return values_input


def get_config():
    """

    :return:
    :rtype:
    """
    pd.set_option('mode.chained_assignment', None)
    print("Loading data")
    values_input = import_from_sheets()
    df = pd.DataFrame(values_input[1:], columns=values_input[0])

    print("Transforming data")
    monsters_df = df[["name", "type"]]
    monsters_df["type"] = pd.to_numeric(df["type"])

    triggers = df.drop(['name', 'role', 'type', 'id'], axis=1)
    triggers = triggers.applymap(lambda s: s.lower() if type(s) == str else s)
    # triggers = triggers.applymap(lambda s: unidecode.unidecode(s) if type(s) == str else s)

    triggers_list = []
    for row in triggers.itertuples(index=False):
        helpt = pd.Series(row)
        helpt = helpt[~helpt.isna()]
        # Drop empty strings
        helpt = pd.Series(filter(None, helpt))
        # Copy strings with spaces without keeping them
        for trigger in helpt:
            trigger_nospace = trigger.replace(' ', '')
            helpt = helpt.append(pd.Series(trigger_nospace))
        helpt = helpt.drop_duplicates()
        triggers_list.append(helpt)

    print("Creating trigger structure")
    triggers_def = []
    for i in triggers_list:
        triggers_def.append(list(i))
    triggers_def_series = pd.Series(triggers_def)
    monsters_df.insert(loc=0, column='triggers', value=triggers_def_series)

    print("Creating output")
    types = {'id': [4, 3, 2, 1, 0], 'label': ["Common", "Event0", "Event1", "Legendary", "Rare"]}
    types_df = pd.DataFrame(data=types)
    milestones = {"Rare Spotter": [150], "tescior": 151, "Pepega Spotter": [1000], "Pog Spotter": [2000], "Pogmare Spotter": [3000],
                  "Legendary Spotter": [4000], "Mythic Spotter": [5000]}
    milestones_df = pd.DataFrame(data=milestones)
    json_final = {'milestones': milestones_df, 'types': types_df, 'commands': monsters_df}

    # convert dataframes into dictionaries
    data_dict = {
        key: json_final[key].to_dict(orient='records')
        for key in json_final
    }

    # write to disk
    with open('server_files/config.json', 'w', encoding='utf8') as f:
        json.dump(
            data_dict,
            f,
            indent=4,
            ensure_ascii=False,
            sort_keys=False
        )
    print(".json saved")


def main():
    get_config()


if __name__ == "__main__":
    main()
