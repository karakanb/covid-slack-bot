import logging
import os
from helpers import JsonBin, CovidApi, Slack

def getEnvOrFail(key: str):
  value = os.environ.get(key)
  if value is None:
    raise ValueError(f"The key '{key}' is a required environment variable, you cannot run the application without it.")

  return value

def getChangedCountries(newList: list, oldList: list) -> bool:
  newCountries = {c['country'] for c in newList if 'country' in c}
  oldCountries = {c['country'] for c in oldList if 'country' in c}
  return newCountries.difference(oldCountries) 

def main():
  # collect the env variables before starting the process
  COVID_API_URL = getEnvOrFail('COVID_API_URL')
  COVID_API_UI_URL = getEnvOrFail('COVID_API_UI_URL')
  COVID_API_MAX_RETRIES = int(getEnvOrFail('COVID_API_MAX_RETRIES'))
  
  COVID_RISK_THRESHOLD = float(getEnvOrFail('COVID_RISK_THRESHOLD'))
  COVID_RISK_RESPONSE_KEY = getEnvOrFail('COVID_RISK_RESPONSE_KEY')
  
  SLACK_WEBHOOK_URL = getEnvOrFail('SLACK_WEBHOOK_URL')
  SLACK_USERNAME = getEnvOrFail('SLACK_USERNAME')
  SLACK_ICON_EMOJI = getEnvOrFail('SLACK_ICON_EMOJI')
  
  JSON_BIN_URL = getEnvOrFail('JSON_BIN_URL')
  JSON_BIN_SECRET = getEnvOrFail('JSON_BIN_SECRET')

  LOG_LEVEL = getEnvOrFail('LOG_LEVEL')

  logging.basicConfig(format='%(asctime)s  %(name)s  %(levelname)s: %(message)s', level=LOG_LEVEL.upper())
  logger = logging.getLogger('app')

  logger.info('collected all the env variables, starting the process.')

  # build the helper classes
  jsonBin = JsonBin(JSON_BIN_URL, JSON_BIN_SECRET)
  covidApi = CovidApi(COVID_API_URL, COVID_API_MAX_RETRIES)
  slack = Slack(SLACK_WEBHOOK_URL, SLACK_USERNAME, SLACK_ICON_EMOJI, COVID_API_UI_URL, COVID_RISK_RESPONSE_KEY, COVID_RISK_THRESHOLD)

  # fetch the risk countries from the API to begin with.
  logger.info("fetching the covid api response.")
  riskCountries = covidApi.fetch(COVID_RISK_RESPONSE_KEY, COVID_RISK_THRESHOLD)
  if len(riskCountries) == 0:
    logger.warning("there are no countries that have any risk, bailing.")
    return
 
  logger.info(f"{len(riskCountries)} countries have '{COVID_RISK_RESPONSE_KEY}' value greater than or equal to {COVID_RISK_THRESHOLD}.")

  # fetch the previous records to compare the last run with the current one.
  logger.info("fetching the jsonbin record.")
  previousCountries = jsonBin.fetch()

  # get the difference, if there is no change let the slack channel know.
  newCountries = getChangedCountries(riskCountries, previousCountries)
  if len(newCountries) == 0:
    logger.warning("the list hasn't changed, bailing.")
    slack.sendNoChangeNotification(len(riskCountries))
    return

  # if the data has changed then update the jsonbin.
  jsonBin.update(riskCountries)
  logger.info("updated the json bin.")

  # update the slack channel with the latest list.
  slack.sendChangedNotification(riskCountries, newCountries)
  logger.info("sent the slack notification.")

if __name__ == "__main__":
  main()