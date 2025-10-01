import pickle
import os.path
import json
import requests 
import re 
import html
from googleapiclient.discovery import build 
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials   
import logging



# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
lo = logging.getLogger("GMailMapper")

class Gmail():
    """Class to handle GMail API interactions, including fetching of and threads.

    Args:
        `user_email` (str): The email address of the user to fetch emails for
        `friendly_name` (str): A friendly name for the user
        `token` (google.oauth2.credentials.Credentials): A valid token object
        `token_file_path` (str): The path to the token file to load. If not provided, the token object must be provided.
        `refresh_token` (str): OAuth2 refresh token to create credentials from
        `client_id` (str): OAuth2 client ID (required if using refresh_token)
        `client_secret` (str): OAuth2 client secret (required if using refresh_token)"""
    def __init__(self, user_email, friendly_name, token:Credentials = None, token_file_path=None, refresh_token=None, client_id=None, client_secret=None) -> None:
        logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.WARNING)

        # Handle different authentication methods in order of priority
        if token is not None:
            # Use provided credentials object directly
            self.credentials = token
        elif token_file_path is not None:
            # Load credentials from file
            self.credentials = load_token(token_file_path)
        elif refresh_token is not None and client_id is not None and client_secret is not None:
            # Create credentials from refresh token
            self.credentials = make_new_token_from_refresh_bits(refresh_token, client_id, client_secret)
        else:
            raise ValueError("Must provide either 'token', 'token_file_path', or 'refresh_token' with 'client_id' and 'client_secret'")

        self.friendly_name = friendly_name
        self.user_email = user_email
        self.service = self.build_service()
        pass            





    def list_threads_matching_query(self, query='label:UNREAD label:INBOX'):

        
        """List all Threads of the user's mailbox matching the query.  The query should be formatted the same as you would use in the GMail search box.  
        For more info on query formatting see https://support.google.com/mail/answer/7190?hl=en
        
        Args:
            `service` (googleapiclient.discovery.Resource): The gmail service object
            `user_id` (str): The email address of the user to fetch emails for
            `query` (str): The query to use to filter the emails. Defaults to 'label:UNREAD label:INBOX'
            """
        service = self.service
        user_id = "me"
        try:
            response = service.users().threads().list(userId=user_id, q=query).execute()
            threads = []
            if 'threads' in response:
                threads.extend(response['threads'])

            while 'nextPageToken' in response:
                page_token = response['nextPageToken']
                response = service.users().threads().list(userId=user_id, q=query,
                                                    pageToken=page_token).execute()
                threads.extend(response['threads'])

            return threads
        except Exception as error:
            print ('An error occurred: %s' % error)



    def build_service(self): 
        """Builds the service object for the gmail API.  This is used to make calls to the API.
        
        Returns:
            `googleapiclient.discovery.Resource`: The gmail service object"""
        self.service = build('gmail', 'v1', credentials=self.credentials)
        return self.service

def load_token( file_path = None) -> Credentials:
    load_pickled_credentials(file_path)
    
def load_pickled_credentials( file_path = None) -> Credentials:
    "Gets valid user credentials from pickled storage."
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    #print(os.getcwd()+filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as token:
            creds = pickle.load(token)
            
    else:
        raise FileNotFoundError(f"No token file found at {file_path}")
    
    # If there are no (valid) credentials available flag the error so the user can re-auth
    if not creds or not creds.valid:
        lo.warning ("Saved token no longer valid - need to re-auth")
        raise InvalidCredentialsException(f"Valid credentials could not be found at {file_path}")
    return creds

def make_new_credentials(client_secrets_str:str, redirect_uri = "https://127.0.0.1/") -> Credentials:
    client_secrets = json.loads(client_secrets_str)

    flow = InstalledAppFlow.from_client_config(client_secrets, SCOPES, redirect_uri=redirect_uri)
    
    creds = flow.run_local_server( open_browser=True, host="localhost",port=8080)
    return creds


def make_new_token(client_secrets_file:str, redirect_uri = "https://127.0.0.1/") -> Credentials:
    "builds new token and dumps it to file, then returns"
    try:
        with open(client_secrets_file, "r", encoding="UTF-8") as f:
            client_secrets_str = f.read()
    except (FileNotFoundError) as err:
        logging.warning(f"Unable to open  client secrts file {err}")
        return None
    return make_new_credentials(client_secrets_str, redirect_uri)
    
def make_new_token_from_refresh_bits(refresh_token:str, client_id:str, client_secret:str, token_uri:str = "https://oauth2.googleapis.com/token") -> Credentials:
    "builds new token and dumps it to file, then returns"

    creds = Credentials("token",refresh_token, token_uri=token_uri, client_id=client_id, client_secret=client_secret)
    creds.refresh(Request())
    return creds


def save_token(token: Credentials, file_path:str):
    "Saves the token to file"
    with open(file_path, 'wb') as token_file:
        pickle.dump(token, token_file)


def extract_clientid_clientsecret_from_secretjson(secret_json:str) -> tuple:
    """Extracts the client id and secret from the secret json file
    
    Args:
        `secret_json` (str): The contents of the secret json file (as a string)

    Returns:
        `tuple(str,str)`: A tuple containing the client id and secret"

    """
 
    data = json.loads(secret_json)
    return (data["installed"]["client_id"], data["installed"]["client_secret"])

class InvalidCredentialsException(BaseException): 
    "Exception raised when credentials are invalid/ expired"


if __name__ == "__main__":
    f_name = "oauth_token.secret"
    credentials_filename = "gcloud_secrets.secret"
    try:
        token = load_pickled_credentials(f_name)
    except (InvalidCredentialsException, FileNotFoundError) as err:
        with open(f_name, "wb+") as f:
            token = make_new_token(credentials_filename)
            pickle.dump(token, f)
    imp = input("enter Y if you'd like the refresh token outputted to console. \n Useful during first time setup.")
    if imp.upper() == "Y":
        print(token.refresh_token)
    
    
        