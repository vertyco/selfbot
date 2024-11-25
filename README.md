# Userbot Ad Poster

This project is a Python-based userbot that utilizes the `discord.py-self` library to make scheduled posts in Discord servers.

## Disclaimer

This project is intended for educational purposes only. The author is not responsible for any misuse or violations of Discord's Terms of Service (ToS) that may occur through the use of this software. Users are advised to ensure compliance with all relevant rules and obtain necessary permissions before deploying the bot.

## Features

- **Automated Ad Posting**: Schedule and post advertisements in designated channels accross multiple servers.
- **Customizable Settings**: Configure the bot to post at specific intervals. Supports forums too.

## Quickstart

- Download the executable file from the releases page.
- Put it somewhere in a folder on your desktop.
- Create a `.env` file in the same folder as the executable.
- Add the following to the `.env` file:

```env
TOKEN=your_user_token_here
SENTRY_DSN=your_sentry_dsn_here (Optional)
```

- Create a folder called `ads`
- In your ads folder, create a new folder for the server you want to post ads in.
- In that folder, create a new file called `content.txt`
- Add the content of your ad to the `content.txt` file.
- In that same folder, create a new file called `configy.py`
- Add the following to the `configy.py` file:

```python
enabled = True  # Whether the ad is enabled
channel_id = 1234567891234567890  # ID of the channel to post the ad in
cooldown_minutes = 360  # How many minutes (roughly) to wait between posts

# Forum Channel Specific (These must be included but can be left blank if not a forum)
title = ""  # The title of the forum
tags = [1234567891234567890]  # List of form tag IDs you want the post to have selected
```

- Any pictures you want included in the ad can be placed in the same folder as the `configy.py` file.

Your file structure should now look like this:

```
- ads
    - server1
        - content.txt
        - configy.py
        - picture1.png
    - server2
        - content.txt
        - configy.py
        - picture1.png
- .env
- SelfBot.exe
```

- Run the executable file.

This will start the bot and begin posting ads in the designated channels at the specified intervals. It will create a file called `db.json` where it keeps track of its last post times, which means you can stop and start the bot without losing your place.

Alternatively, you can pull down the repo and install the dependencies with `pip install -r requirements.txt` and run the bot with `python main.py` after setting up the `.env` file and the `ads` folder.
