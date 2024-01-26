# ☕️ CoffeeBot 🤖

<img width="500" alt="Screenshot" src="https://github.com/justinh-rahb/CoffeeBot/assets/52832301/db64049e-795c-4ed1-9700-a9a01152bbed">
<br>
<img width="500" alt="Screenshot 2024-01-24 at 8 36 18 PM" src="https://github.com/justinh-rahb/CoffeeBot/assets/52832301/32cf06c4-b590-4fb2-bb35-21503205cbe3">


This is a bot 🤖, that watches the pot 🫖, and reminds you if you forgot 🤷‍♂️.

### Table of Contents
* [Requirements](#requirements)
* [Installation](#installation)
* [Configuration](#configuration)
* [Never Lose Your Coffee Again!](#never-lose-your-coffee-again)
* [License](#license)

## Requirements

* Python 3.6 or higher 🐍
* Webcam 📷
* Computer (even a potato 🥔 with 4GB RAM should do, as long as it runs Linux 🐧)
* Coffee machine 🫖
* Coffee cup ☕️
* Propensity to forget your cup at the coffee machine 🤔

## Installation

1. Clone this repository with `git clone https://github.com/justinh-rahb/CoffeeBot.git`
2. Move the cloned repository to `/opt` with `sudo mv CoffeeBot /opt`
3. `cd` into the cloned repository with `cd /opt/CoffeeBot`
4. Install the requirements with `sudo pip3 install -r requirements.txt`
5. Set your environment variables by copying `.env.example` with `sudo cp .env.example .env` and editing `.env` with your favorite editor
6. Copy the systemd service file to `/etc/systemd/system` with `sudo cp coffeebot.service /etc/systemd/system`
7. Reload the systemd daemon with `sudo systemctl daemon-reload`
8. Launch the bot with `sudo systemctl start coffeebot.service`

## Configuration

The bot is configured via environment variables. You can set them in the `.env` file, or directly in your shell.

| Variable | Description | Default |
| -------- | ----------- | ------- |
| BOT_WEBHOOK_URL | webhook URL for the bot to send messages to | none |
| BOT_MESSAGE | message to send when the object is detected | Coffee cup left unattended! Please remove it from the coffee machine :) |
| OBJECT | object to detect (see list: [coco.names](https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names)) | cup |
| MIN_CONFIDENCE | minimum confidence level for object detection | 0.5 |
| FRAME_SKIP | number of frames to skip before checking for object | 5 |
| DETECTION_TIME | time in seconds object must be detected before sending message | 300 |
| CAPTURE_DEVICE | 0 for default webcam, 1 for USB webcam | 0 |
| SAVE_DIR | directory to save images | /tmp |

## Never Lose Your Coffee Again!
Your coffee machine monitoring system should be up and running, so your co-workers won't have to remind you to get your cup anymore, and you can enjoy your coffee while it's still hot.

## License
This project is open sourced under the MIT license. See the [LICENSE](LICENSE) file for more info.
