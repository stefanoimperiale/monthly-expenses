# Monthly expense tracker
[![](https://badgen.net/badge/icon/github?icon=github&label)](https://github.com/stefanoimperiale/monthly-expenses)
[![](https://badgen.net/badge/icon/docker?icon=docker&label)](https://hub.docker.com/r/stefanoimperiale/monthly-expenses)
[![Docker Pulls](https://badgen.net/docker/pulls/stefanoimperiale/monthly-expenses?icon=docker&label=pulls)](https://hub.docker.com/r/stefanoimperiale/monthly-expenses)
[![Docker Stars](https://badgen.net/docker/stars/stefanoimperiale/monthly-expenses?icon=docker&label=stars)](https://hub.docker.com/r/stefanoimperiale/monthly-expenses)
[![Docker Image Size](https://badgen.net/docker/size/stefanoimperiale/monthly-expenses?icon=docker&label=image%20size)](https://hub.docker.com/r/stefanoimperiale/telethon_downloader)
![Github stars](https://badgen.net/github/stars/stefanoimperiale/monthly-expenses?icon=github&label=stars)
![Github forks](https://badgen.net/github/forks/stefanoimperiale/monthly-expenses?icon=github&label=forks)
![Github last-commit](https://img.shields.io/github/last-commit/stefanoimperiale/monthly-expenses)
![Github last-commit](https://badgen.net/github/license/stefanoimperiale/monthly-expenses)

## Find us at:

[![github](https://img.shields.io/badge/github-stefanoimperiale-5865F2?style=for-the-badge&logo=github&logoColor=white&labelColor=101010)](https://github.com/stefanoimperiale/monthly-expenses)
[![docker](https://img.shields.io/badge/docker-stefanoimperiale-5865F2?style=for-the-badge&logo=docker&logoColor=white&labelColor=101010)](https://hub.docker.com/r/stefanoimperiale/monthly-expenses)

<p align="center">
    <img src="https://github.com/stefanoimperiale/monthly-expenses/blob/master/images/logo.png?raw=true" alt="alt text" width="25%">
</p>

# [stefanoimperiale/monthly-expenses](https://github.com/stefanoimperiale/monthly-expenses)

## Description

This is a simple telegram bot expense tracker that allows you to add, edit and delete expenses. It use a Google Drive
spreadsheet as a database.

## Functionality

- Add expense in telegram chat
- Edit expense in telegram chat
- Delete expense in telegram chat
- Show expenses in telegram chat
- Retrieve all monthly expenses in image format
- Retrieve all monthly expenses in pie chart format
- Save recurring expenses and automatically add them to the new spreadsheet
- (Optional) [Wise](https://wise.com/) integration: automatically add a new expense when a new transaction is made on your Wise account

![](images/example.gif)
![](images/sheet.png)


## Installation

1. Create a new telegram bot using BotFather
2. Create a new Google Drive spreadsheet
3. Create a new Drive API service account and download the JSON file
4. Share the spreadsheet with the service account email
5. Create a new spreadsheet and share it with the service account email

# Generating Telegram API keys

Before working with Telegram's API, you need to get your own API ID and hash:

1. Go to https://my.telegram.org/ and login with your
   phone number.

2. Click under API Development tools.

3. A *Create new application* window will appear. Fill in your application
   details. There is no need to enter any *URL*, and only the first two
   fields (*App title* and *Short name*) can currently be changed later.

4. Click on *Create application* at the end. Remember that your
   **API hash is secret** and Telegram won't let you revoke it.
   Don't post it anywhere!

# Creating a Telegram Bot

1. Open a conversation with [@BotFather](https://telegram.me/botfather) in Telegram

2. Use the /newbot command to create a new bot. The BotFather will ask you for a name and username, then generate an
   authorization token for your new bot.

   The name of your bot is displayed in contact details and elsewhere.

   The Username is a short name, to be used in mentions and telegram.me links. Usernames are 5-32 characters long and
   are case insensitive, but may only include Latin characters, numbers, and underscores. Your bot's username must end
   in ‘bot’, e.g. ‘tetris_bot’ or ‘TetrisBot’.

   The token is a string along the lines of 110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw that is required to authorize
   the bot and send requests to the Bot API. Keep your token secure and store it safely, it can be used by anyone to
   control your bot.

# Wise Integration
In order to enable Wise integration you need to create a new Wise Webhook. 
You can do it from [here](https://wise.com/settings/webhooks).


curl -X GET https://api.sandbox.transferwise.tech/v4/profiles/P56202086/balances?types=STANDARD \
-H 'Authorization: Bearer c61d6c7d-cbe1-431a-a484-ab493af05844'

curl -X GET "https://api.transferwise.com/v3/profiles/{{profileId}}/subscriptions/{{subscriptionId}}" \
-H 'Authorization: Bearer c61d6c7d-cbe1-431a-a484-ab493af05844'

## Environment variables

|              Environment              | Function                                                                     | Default Value |   
|:-------------------------------------:|------------------------------------------------------------------------------|---------------|
|              `CURRENCY`               | (Optional) the currency used in application                                  | EUR           |
|              `TG_API_ID`              | telegram API key generated at ´Generating Telegram API keys´                 | [REQUIRED]    |
|             `TG_API_HASH`             | telegram API hash generated at ´Generating Telegram API keys´                | [REQUIRED]    |
|            `TG_BOT_TOKEN`             | telegram BOT token generated at ´Creating a Telegram Bot´                    | [REQUIRED]    |
|           `SPREADSHEET_ID`            | Id of the Google Drive Spreadsheet, you can retrieve it from url             | [REQUIRED]    |
|               `USER_ID`               | The autorized telegram user ID                                               | [REQUIRED]    |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | The Google JSON credential file generated when created a new service account | [REQUIRED]    |

## Note

On new year you need to create a new spreadsheet and share it with the service account email. Then you need to update
the `SPREADSHEET_ID` environment variable with the new spreadsheet id.

### Run with docker

```yaml
version: "3"
services:
  monthly-expenses:
    privileged: true
    image: stefanoimperiale/monthly-expenses
    container_name: monthly-expense-tracker
    restart: unless-stopped
    environment:
      - CURRENCY=EUR
      - TG_API_ID=123456
      - TG_API_HASH=123456
      - TG_BOT_TOKEN=123456
      - SPREADSHEET_ID=123456
      - USER_ID=123456
      - GOOGLE_APPLICATION_CREDENTIALS_JSON='{JSON-FILE-CONTENT}'
```
