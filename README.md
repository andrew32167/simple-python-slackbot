# simple-python-slackbot
Simple to start and maintain your personal slackbot.
The main stuff is about `Bot` class at `Bot.py` that simplifies slackbot integration
# Installation
Create new virtual environment clone repo there and install necessary packages
```
virtualenv simple-python-slackbot
cd simple-python-slackbot
source bin/activate
git clone git@github.com:andrew32167/simple-python-slackbot.git
pip install -r simple-python-slackbot/requirements.txt
```
# Usage
Just import Bot class and pass `token` and `bot_id` to constructor and you're ready to go
```
from Bot import Bot
    
bot = Bot(bot_token='YOUR_BOT_TOKEN',
          bot_id='YOUR_BOT_ID')
          

```