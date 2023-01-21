Bot to catch recent earthquakes
===============================

This bot uses the USGS (United States Geological Survey) API to catch recent earthquakes. The bot checks earthquakes that occurred in the last 5 minutes, and if it finds an earthquake that occurred within 50 km of Kusadasi, Turkey, it sends a message to a Telegram chat with information about the earthquake. The message includes the place, magnitude, time and a image of the event.

Getting started
---------------

### Prerequisites

-   Python 3.8
-   AWS Lambda (if you plan to deploy on AWS)

### Installing

Clone the repository:

`git clone https://github.com/twentythousandphantoms/bots/tree/main/earthquakes`


### Configuration

Rename config.py.example to config.py

Edit the config.py file:

```
TELEGRAM_TOKEN = 'YOUR_TELEGRAM_TOKEN'
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
```

CHAT_ID:
- it could ba a public/private group chat. The telegram bot should be a member of this chat in order to send messages there
- it could be a channel as well. The telegram bot should be added with admin rights in order be able to publish messages in this channel


### Run the bot

You can run the bot with this command:

`python3 main.py`

### Deployment on AWS Lambda

You can deploy this bot on AWS Lambda. For this, you need to create a zip file of the bot's code and dependencies.

Create a zip file:

`zip -r function.zip .`

In your AWS Lambda function configuration, you can select "Upload a .zip file" as the package type and upload the function.zip file you created.  
If everything is working as expected, you can set up a CloudWatch Event to trigger the Lambda function to run on a schedule (e.g. every 5 minutes).

### Using environment variable

If you don't want to include your Telegram token in the code, you can set the `TELEGRAM_TOKEN` environment variable in your AWS Lambda function configuration.