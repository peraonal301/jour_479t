# importing the libraries we need to run this script
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
from bs4 import BeautifulSoup
import datetime
import re

# URL to check for agendas
AGENDA_URL = "https://www.collegeparkmd.gov/agendacenter"

# File to store the last agenda date
LAST_DATE_FILE = "last_agenda_date.txt"

def get_latest_agenda_date():
    try:
        response = requests.get(AGENDA_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Get all text from the page
        text = soup.get_text()
        # Find dates in format like "January 15, 2024" or "Jan 15, 2024"
        date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b'
        matches = re.findall(date_pattern, text)
        if matches:
            dates = []
            for match in matches:
                # Normalize month names to full for strptime
                match = re.sub(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b', lambda m: {
                    'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Apr': 'April', 'May': 'May', 'Jun': 'June',
                    'Jul': 'July', 'Aug': 'August', 'Sep': 'September', 'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
                }[m.group()], match)
                try:
                    date = datetime.datetime.strptime(match, '%B %d, %Y').date()
                    dates.append(date)
                except ValueError:
                    pass
            if dates:
                return max(dates)
        return None
    except Exception as e:
        print(f"Error fetching agenda: {e}")
        return None

# this is pulling that secret we added earlier
slack_token = os.environ.get('SLACK_API_TOKEN')

# telling slack we want to interact with it using our key
client = WebClient(token=slack_token)

# message we want to send
# swap out the brackets for your name, or change the message entirely
msg ="The agenda for the College Park City Council meeting has been published! Check it out here: <https://www.collegeparkmd.gov/agendacenter|College Park City Council Agendas & Minutes>"

# Check for new agenda
latest_date = get_latest_agenda_date()
if latest_date:
    # Read last known date
    last_date = None
    if os.path.exists(LAST_DATE_FILE):
        try:
            with open(LAST_DATE_FILE, 'r') as f:
                last_date_str = f.read().strip()
                last_date = datetime.datetime.strptime(last_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if last_date is None or latest_date > last_date:
        # New agenda published, send message
        try:
            response = client.chat_postMessage(
                channel="jour479t", # this is the channel the message will send to
                text=msg,
                unfurl_links=True, 
                unfurl_media=True
            )
            # if the message is sent, then print the word success!
            print(f"Success! New agenda detected (date: {latest_date}). Message sent.")
            # Update last date
            with open(LAST_DATE_FILE, 'w') as f:
                f.write(latest_date.strftime('%Y-%m-%d'))
        except SlackApiError as e:
            assert e.response["ok"] is False
            assert e.response["error"]
            print(f"Got an error: {e.response['error']}")
    else:
        print(f"No new agenda. Latest date: {latest_date}, Last checked: {last_date}")
else:
    print("Could not retrieve latest agenda date.")

# To run this script automatically every time a new agenda is published,
# set up a cron job to run it periodically (e.g., every hour).
# Example: crontab -e and add "0 * * * * cd /workspaces/jour_479t && python3 week10/slackbot.py"
# This way, it checks for new agendas on schedule and sends a message only when one is detected.
import time
while True:
    # The existing check code here (you can wrap the check logic in a function)
    time.sleep(3600 * 24)  # Sleep for 24 hours (adjust as needed, e.g., 86400 seconds for 24 hours)
