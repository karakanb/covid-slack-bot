# ECDC-based COVID-19 High-risk Countries Slack Bot
This is a simple Python application that will fetch the country stats from European Centre for Disease Prevention and Control (ECDC) and sends a list of high-risk countries to the given Slack webhook.

## Usage
- Create a `.env` file based on the provided `.env.example` file.
- Run `docker-compose up`
- Exec into the container: `docker exec -it <CONTAINER_NAME> -- bash`
- Run the script: `python app.py`

That's it.
