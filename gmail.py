import pickle
import os.path
import json
import requests 
import re 
import html
from googleapiclient.discovery import build 
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import logging



# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
lo = logging.getLogger("GMailMapper")

class Gmail():
    def __init__(self, user_email,friendly_name) -> None:
        logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.WARNING)
        self.token = self._getToken(friendly_name)
        self.friendly_name = friendly_name
        self.user_email = user_email
        pass            





    def list_threads_matching_query(self,service, user_id, query='label:UNREAD label:INBOX'):
        
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

    def _getToken(self,tokenName):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        filename = "resources/GMailAuthTokens/%s.pickle" % (tokenName)
        #print(os.getcwd()+filename)
        if os.path.exists(filename):
            with open(filename, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            lo.warning ("Needing authorisation for the %s inbox!" % (tokenName))
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                lo.warning ("Needing authorisation for the %s inbox!" % (tokenName))
                flow = InstalledAppFlow.from_client_secrets_file(
                    'resources/GMailCredentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(filename, 'wb') as token:
                pickle.dump(creds, token)
        return creds


    def fetch_gmail_items(self):
        """
        Lists the user's emails that are in the inbox.
        """
        service = build('gmail', 'v1', credentials=self.token)
        threads = self.list_threads_matching_query(service,"me")
        return threads


