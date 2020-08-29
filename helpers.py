import datetime
import logging
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class JsonBin:
  def __init__(self, url: str, secret: str):
    self.url = url
    self.secret = secret
    self.headers = {
      'secret-key': self.secret,
      'Content-Type': 'application/json'
    }

    self.logger = logging.getLogger('client.jsonbin')
  
  def fetch(self) -> list:
    self.logger.debug('fetching the data from the bin')
    response = requests.request("GET", f"{self.url}/latest", headers=self.headers)
    self.logger.debug('successfully fetched the data')
    
    return response.json()

  def update(self, new: list) -> None:
    self.logger.debug('updating the bin')
    requests.put(self.url, json=new, headers=self.headers)
    self.logger.debug('successfully updated the bin')


class CovidApi:
  def __init__(self, url: str, retries: int):
    self.url = url
    self.retries = retries
    self.logger = logging.getLogger('client.covid-api')
  
  def fetch(self, riskResponseKey: str, riskThreshold: str) -> list:
    self.logger.debug('configuring the retry adapter for the http client')
    retry_strategy = Retry(total=self.retries, status_forcelist=[429, 500, 502, 503, 504], backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    self.logger.debug('the http client configured successfully')

    self.logger.debug('fetching the country list')
    response = http.get(self.url).json()
    self.logger.debug('fetched the country list')
    return list(filter(lambda c: c[riskResponseKey] >= riskThreshold, response))
    

class Slack:
  def __init__(self, webhookUrl: str, username: str, iconEmoji: str, covidApiUiUrl: str, covidRiskResponseKey: str, covidRiskThreshold: str):
    self.webhookUrl = webhookUrl
    self.username = username
    self.iconEmoji = iconEmoji
    self.uiUrl = covidApiUiUrl
    self.covidRiskResponseKey = covidRiskResponseKey
    self.covidRiskThreshold = covidRiskThreshold
    self.logger = logging.getLogger('client.slack')
  
  def sendChangedNotification(self, countries: list, newCountries: set) -> None:
    self.logger.debug(f'sending the changed list notification to slack for {len(countries)} with {len(newCountries)} new countries')
    text = f"The list of COVID-19 risk countries have changed, the updated list is below:\n\n\n"
    text += f"*Criteria:* `{self.covidRiskResponseKey} >= {self.covidRiskThreshold}`\n\n"
    text += "*Countries:*\n"
    
    for c in countries:
      text += f"• {c['country']}: `{c[self.covidRiskResponseKey]}` { ' :new:' if c['country'] in newCountries else '' }\n"
    
    text += f"\n<{self.uiUrl}|Check out the full list of high risk countries here.>"
    self.__sendMessage(text)

  def sendNoChangeNotification(self, countryCount: int) -> None:
    self.logger.debug(f"sending 'no changes occurred' message to slack")
    text = f"The list of COVID-19 risk countries doesn't seem to have changed, there are currently {countryCount} countries in the list. "
    text += f"<{self.uiUrl}|Check out the full list of high risk countries here.>"
    self.__sendMessage(text)

  def __sendMessage(self, text: str) -> None:
    self.logger.debug('sending api call to slack')
    response = requests.post(self.webhookUrl, json={'text': text, 'username': self.username, 'icon_emoji': self.iconEmoji}, headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
      raise ValueError(f'Request to slack returned an error {response.status_code}, the response is:\n{response.text}')

