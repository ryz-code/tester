import re
import pytz
import string
import secrets
import requests
from os import getenv
from drive1bot import OneDriveLog
from urllib.parse import quote
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timedelta

load_dotenv()
log = OneDriveLog()

class MicrosoftGraphAuth:
    AUTH_URI = getenv("AUTH_URI")
    DRIVE_URI = getenv("DRIVE_URI")
    SCOPES = getenv("SCOPES")
    
    def __init__(self):
        self.client_id = getenv('CLIENT_ID')
        self.redirect_uri = getenv('REDIRECT_URI')
        self.client_secret = getenv('CLIENT_SECRET_VALUE')
        self.refresh_token = None
        self.access_token = None
        self.expires_in = None
        self.current_timezone = pytz.timezone('Asia/Kolkata')
        
        # mongodb
        self.mongo_client = MongoClient(getenv('MONGO_URI'))
        self.db = self.mongo_client["1drivebot"]
        self.auth_tokens = self.db["auth_tokens"]
        
        
    def update_tokens(self, refresh_token, access_token):
        self.auth_tokens.update_one(
            {"_id": "auth_tokens"},{
                "$set": {
                    "refresh_token": refresh_token,
                    "access_token": access_token,
                }
            },
            upsert=True
        )


    def get_auth_code(self):
        state = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
        request_uri = f"{self.AUTH_URI}/authorize?client_id={self.client_id}&response_type=code&redirect_uri={quote(self.redirect_uri, safe='')}&response_mode=query&scope={quote(self.SCOPES)}&state={state}"
        print(request_uri)
        response = input("paste the response here: ")
        auth_code = re.search(r'code=([^&]+)', response)
        
        if auth_code is None:
            return "The response does not contain an auth code"
        
        return auth_code.group(1)
        
        
    def get_token(self):
        if tokens := self.auth_tokens.find_one({"_id": "auth_tokens"}):
            self.refresh_token = tokens.get("refresh_token", "")
            
        data = {
            "client_id": self.client_id,
            "scope": self.SCOPES,
            "redirect_uri": self.redirect_uri,
            "client_secret": self.client_secret,
        }
        
        if self.refresh_token is None:
            data["code"] = self.get_auth_code()
            data["grant_type"] = "authorization_code"
        else:
            data["refresh_token"] = self.refresh_token
            data["grant_type"] = "refresh_token"

        response = requests.post(f"{self.AUTH_URI}/token", data=data)
        token_info = response.json()
        self.access_token = token_info['access_token']
        self.refresh_token = token_info['refresh_token']
        self.expires_in = token_info['expires_in'] - 60
        
        self.update_tokens(self.refresh_token, self.access_token)
        
        return self.access_token, self.refresh_token, self.expires_in

    def check_and_refresh_token(self):
        if not self.access_token or not self.expires_in:
            self.get_token()
            
            
        if self.expires_in < 300:
            print("Access token is about to expire. Refreshing...")
            self.get_token()
            # print("Refresh Token:", self.refresh_token)
            self.auth_tokens.update_one(
                {"_id": "auth_tokens"},
                {"$set": {"refresh_token": self.refresh_token}}
            )
            
        expire = datetime.now() + timedelta(seconds=self.expires_in)
        access_token_expires = expire.astimezone(self.current_timezone)
        formatted_expires = access_token_expires.strftime("%I:%M:%S %p - %d/%m/%Y")
        print("Access Token Expires:", formatted_expires)
    
    def headers(self):
        access_token, _, _ = self.get_token()
        header = {
            "Accept": "*/*",
            "Authorization": f"Bearer {access_token}",
        }
        return header