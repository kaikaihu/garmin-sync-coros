import logging
import os
from enum import Enum, auto
import requests

import garth


from .garmin_url_dict import GARMIN_URL_DICT

logger = logging.getLogger(__name__)


class GarminClient:
  def __init__(
      self,
      email,
      password,
      auth_domain,
      newest_num,
      garth_token=None,
      allow_password_login=True,
      garth_client=None,
  ):
        self.auth_domain = auth_domain
        self.email = email
        self.password = password
        self.garthClient = garth_client or garth
        self.garth_token = garth_token
        self.allow_password_login = allow_password_login
        self._token_load_attempted = False
        self._token_session_loaded = False
        self._domain_configured = False
        self.newestNum = int(newest_num)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
            "origin": GARMIN_URL_DICT.get("SSO_URL_ORIGIN"),
            "nk": "NT"
        }
  
  def _authenticate(self):
      if (
          not self._domain_configured
          and self.auth_domain
          and str(self.auth_domain).upper() == "CN"
      ):
          self.garthClient.configure(domain="garmin.cn")
          self._domain_configured = True

      if self._token_session_loaded:
          return

      try:
          self.garthClient.client.username
          return
      except Exception:
          logger.warning("Garmin is not logging in or the token has expired.")

      if self.garth_token and not self._token_load_attempted:
          self._token_load_attempted = True
          try:
              self.garthClient.client.loads(self.garth_token)
              if self.garthClient.client.oauth1_token is None:
                  raise GarminOAuth1MissingError()
              self._token_session_loaded = True
              return
          except Exception as err:
              if not self.allow_password_login:
                  raise GarminSessionUnavailableError(
                      "Stored Garmin session could not be restored. "
                      f"Reason: {type(err).__name__}. "
                      "Refusing password login because it is disabled."
                  ) from err

      if not self.allow_password_login:
          raise GarminSessionUnavailableError(
              "No reusable Garmin session is available. "
              "Refusing password login because it is disabled."
          )

      self.garthClient.login(self.email, self.password)

      headers = self.garthClient.client.sess.headers
      headers.pop("User-Agent", None)

  ## 登录装饰器
  def login(func):
    def ware(self, *args, **kwargs):
      self._authenticate()
      return func(self, *args, **kwargs)
    return ware
  
  @login 
  def download(self, path, **kwargs):
     return self.garthClient.download(path, **kwargs)
  
  @login 
  def connectapi(self, path, **kwargs):
      return self.garthClient.connectapi(path, **kwargs)

  @login
  def get_display_name(self):
      """Return Garmin's display name after restoring or creating a session."""
      profile = self.garthClient.client.profile
      if isinstance(profile, dict) and profile.get("displayName"):
          return profile["displayName"]
      return self.garthClient.client.username
     

  ## 获取运动
  def getActivities(self, start:int, limit:int):
     
     params = {"start": str(start), "limit": str(limit)}
     activities =  self.connectapi(path=GARMIN_URL_DICT["garmin_connect_activities"], params=params)
     return activities;

  # ## 获取所有运动
  # def getAllActivities(self): 
  #   all_activities = []
  #   start = 0
  #   limit=100
  #   if 0 < self.newestNum < 100:
  #     limit = self.newestNum
      
  #   while(True):
  #     activities = self.getActivities(start=start, limit=limit)
  #     if len(activities) > 0:
  #       all_activities.extend(activities)
        
  #       if 0 < self.newestNum < 100 or start > self.newestNum:
  #          return all_activities
  #     else:
  #        return all_activities
  #     start += limit

  ## 获取所有运动
  def getAllActivities(self): 
    all_activities = []
    start = 0
    while(True):
      activities = self.getActivities(start=start, limit=100)
      if len(activities) > 0:
         all_activities.extend(activities)
      else:
         return all_activities
      start += 100

  ## 下载原始格式的运动
  def downloadFitActivity(self, activity):
    download_fit_activity_url_prefix = GARMIN_URL_DICT["garmin_connect_fit_download"]
    download_fit_activity_url = f"{download_fit_activity_url_prefix}/{activity}"
    response = self.download(download_fit_activity_url)
    return response

  @login  
  def upload_activity(self, activity_path: str):
    """Upload activity in fit format from file."""
    # This code is borrowed from python-garminconnect-enhanced ;-)
    file_base_name = os.path.basename(activity_path)
    file_extension = file_base_name.split(".")[-1]
    allowed_file_extension = (
        file_extension.upper() in ActivityUploadFormat.__members__
    )

    if allowed_file_extension:
       try:
        with open(activity_path, 'rb') as file:
          file_data = file.read()
          fields = {
              'file': (file_base_name, file_data, 'text/plain')
          }

          url_path = GARMIN_URL_DICT["garmin_connect_upload"]
          upload_url = f"https://connectapi.{self.garthClient.client.domain}{url_path}"
          self.headers['Authorization'] = str(self.garthClient.client.oauth2_token)
          response = requests.post(upload_url, headers=self.headers, files=fields)
          res_code = response.status_code
          result = response.json()
          uploadId =  result.get("detailedImportResult").get('uploadId')
          isDuplicateUpload = uploadId == None or uploadId == ''
          if res_code == 202 and not isDuplicateUpload:
              status = "SUCCESS"
          elif res_code == 409 and result.get("detailedImportResult").get("failures")[0].get('messages')[0].get('content') == "Duplicate Activity.":
              status = "DUPLICATE_ACTIVITY" 
       except Exception as e:
            print(e)
            status = "UPLOAD_EXCEPTION"
       finally:
            return status
    else:
        return "UPLOAD_EXCEPTION"
  

class ActivityUploadFormat(Enum):
  FIT = auto()
  GPX = auto()
  TCX = auto()

class GarminNoLoginException(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, status):
        """Initialize."""
        super(GarminNoLoginException, self).__init__(status)
        self.status = status


class GarminSessionUnavailableError(Exception):
    """Raised when a token-only job has no usable Garmin session."""


class GarminOAuth1MissingError(Exception):
    """Raised when a restored Garmin session has no OAuth1 credential."""
