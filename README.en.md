
## RH Telegram export plugin
This plugin allows you to send the results of the races and laps to Telegram right during the race.
## Features 
+ Sending notifications about the start and finish of races
+ Sending of lap time during the race
+ Sending race results
+ Sending a list of all pilots on the event
+ Sending all event heats
+ Sending a list of pilots in the current heat

# rh_telegram_export
# You need to install the requests library to use it.


## Usage
### 1. Install plugin
Download the plugin as an archive, unzip it and move the rh_telegram_export folder to \src\server\plugins\ 

Enter ```pip install requests``` command in the RH virtual environment to install the required packages

### 2. Creating a bot
To use the plugin you need to create a bot in telegram and get a telegram API token.

To do this, write @BotFather /newbot and follow the bot's instructions, at the end you will receive a token
Example token: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

<b style = "color:red"> !!! WARNING !!! When you shut down and want to export the database, make sure to clear the token field before doing so. </b>
### 3. Interface
![interface](imgs/interface.png)

Go to the "Run" tab and find the "Telegram export" section there.

Insert the token received from botfather into the  "Telegram api token" field.

If you want to send data to a channel, then paste @cannel_name into the input field.

If you want to send data to a group, then copy its telegram id and add -100 before this number (example: -1001234567890)

Now you can customize what information you want to send.

#### Settings
+ **Lap time.**

    If you want to receive data about each completed lap during race, check the box.


+ **Race results**

    This checkbox indicates that you should send the results of the flight immediately after you save the laps after the flight.


+ **Pilots list**

    You can send a list of all pilots or only those with a band and channel (by clicking the checkbox)

+ **Event results**

    It's the same as the race results, but it captures all the pilots and all their laps.

+ **Start and finish notification**

    Select  in the checkbox whether to send a message about the start and finish of the race.
    It contains the name of the group and the round.


Use additional checkboxes to configure

---
