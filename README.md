# CoffeeBot

This is a bot, that watches the pot, and reminds you if you forgot.

## Requirements

* Python 3.6 or higher
* Webcam
* Computer (even a potato should do)
* Coffee machine
* Coffee cup
* Propensity to forget your cup at the coffee machine

## Installation

1. Clone this repository with `git clone https://github.com/justinh-rahb/CoffeeBot.git`
2. Move the cloned repository to `/opt` with `sudo mv CoffeeBot /opt`
3. `cd` into the cloned repository with `cd /opt/CoffeeBot`
4. Install the requirements with `sudo pip3 install -r requirements.txt`
5. Set your environment variables by copying `.env.example` with `sudo cp .env.example .env` and editing `.env` with your favorite editor
6. Copy the systemd service file to `/etc/systemd/system` with `sudo cp coffeebot.service /etc/systemd/system`
7. Reload the systemd daemon with `sudo systemctl daemon-reload`
8. Launch the bot with `sudo systemctl start coffeebot.service`

That's it! Your coffee machine monitoring system should be up and running, so your coworkers won't have to remind you to get your cup anymore, and you can enjoy your coffee while it's still hot.