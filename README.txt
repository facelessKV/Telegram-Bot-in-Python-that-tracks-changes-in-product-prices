📉 Telegram Bot for Tracking Changes in Product Prices

Do you want to monitor changes in product prices effortlessly? This bot will help you not to miss price cuts or increases!
With this bot, you can track the price dynamics for selected products and receive notifications when the price changes.

✅ What can he do?

 • 🛒 Allows you to add links to products for tracking
 • 📈 Automatically tracks price changes
 • 📲 Notifies you of a decrease or increase in the price of an item
 • 📂 Saves data about changes in the database for easy analysis

🔧 Functionality

✅ Easy addition of links to products
✅ Notifications of any price changes
✅ Easy adjustment of the frequency of price checks

📩 Are you ready to start tracking changes in product prices?

Write to me on Telegram and I will help you set up this bot for your business! 🚀

# Instructions for installing and launching a price tracking bot

This bot allows you to track the prices of goods in online stores and notify you of their changes.

## Content
1. [Install for Windows](#install-for-windows)
2. [Install for Linux](#install-for-linux)
3. [Receiving a Telegram Bot token] (#receiving a telegram bot token)
4. [Setting up and launching the bot] (#setting up and launching the bot)
5. [Bot Usage] (#bot usage)

## Installation for Windows

### Step 1: Install Python 3.9
Python 3.9 is a stable version that works great with our bot.

1. Download the Python 3.9 installer from the official website: https://www.python.org/downloads/release/python-3913 /
- Scroll down the page and select "Windows installer (64-bit)"

2. Run the downloaded file and follow the instructions of the installer.:
   - Check the box "Add Python 3.9 to PATH" (this is important!)
- Click "Install Now"

3. Check the installation:
- Open the Command prompt (press Win+R, type cmd and press Enter)
   - Enter the command: `python --version`
   - The Python version should be displayed, for example "Python 3.9.13"

### Step 2: Install the necessary libraries

1. Open the Command Prompt (press Win+R, type cmd and press Enter)

2. Enter the following commands one at a time (press Enter after each one):
   ```
   pip install python-telegram-bot==20.6
   pip install requests
   pip install beautifulsoup4
   ```

### Step 3: Download the bot file

1. Create a new folder for the bot (for example, C:\price-tracker-bot )

2. Save the bot code from previous messages to a file `price_tracker_bot.py ` in the created folder.

## Installation for Linux

### Step 1: Install Python 3.9

1. Open a Terminal (usually Ctrl+Alt+T)

2. Update the package list:
   ```
   sudo apt update
   ```

3. Install the necessary tools to build Python:
   ```
   sudo apt install software-properties-common build-essential
   ```

4. Add a repository with Python 3.9:
``
   sudo add-apt-repository ppa:deadsnakes/ppa
   ```

5. Update the package list again:
   ```
   sudo apt update
   ```

6. Install Python 3.9:
``
   sudo apt install python3.9 python3.9-venv python3.9-dev python3-pip
   ```

7. Check the installation:
``
   python3.9 --version
   ```

### Step 2: Install the necessary libraries

Enter the following commands one at a time:
``
pip3 install python-telegram-bot==20.6
pip3 install requests
pip3 install beautifulsoup4
```

### Step 3: Download the bot file

1. Create a new folder for the bot:
   ```
   mkdir ~/price-tracker-bot
   cd ~/price-tracker-bot
   ```

2. Save the bot code from previous messages to a file `price_tracker_bot.py ` in the created folder.

## Getting a Telegram Bot token

For the bot to work, you need a special token, which you can get from @BotFather on Telegram.:

1. Open Telegram and find the bot @BotFather (Telegram's official bot for creating bots)

2. Write the command to the bot: `/newbot`

3. BotFather will ask you to choose a name for the bot - this name will be displayed to users. For example, "My Price Tracker"

4. Then you need to enter the username for the bot - it should end with "bot". For example, "my_price_tracker_bot"

5. If the name is free, BotFather will give you a token - a long string of characters like:
   ```
   1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
   ```

6. Save this token - you will need it to set up the bot.

## Setting up and launching the bot

### Step 1: Insert the token into the bot code

1. Open the file `price_tracker_bot.py in any text editor (for example, Notepad on Windows or nano on Linux)

2. Find the line:
``python
   application = Application.builder().token("YOUR_TELEGRAM_BOT_TOKEN").build()
   ```

3. Replace `YOUR_TELEGRAM_BOT_TOKEN` with the token received from BotFather (along with quotes), for example:
   ```python
   application = Application.builder().token("1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ").build()
   ```

4. Save the file

### Step 2: Launch the Bot

#### On Windows:
1. Open the Command Prompt (Win+R, type cmd, press Enter)
2. Go to the folder with the bot (for example, `cd C:\price-tracker-bot `)
3. Launch the bot with the command:
   ```
   python price_tracker_bot.py
   ```

#### On Linux:
1. Open A Terminal (Ctrl+Alt+T)
2. Go to the bot folder:
``
   cd ~/price-tracker-bot
   ```
3. Launch the bot with the command:
   ```
   python3.9 price_tracker_bot.py
   ```

### Step 3: Checking the bot's operation

1. Open Telegram on your phone or computer
2. Find the bot by the name you specified when creating it.
3. Write the command `/start` to the bot
4. The bot should reply with a welcome message.

## Using a bot

After launching the bot, you can use the following commands:

- `/start' - Show the greeting and the list of commands
- `/add` - Add a link to the product for tracking
- `/list` - Show a list of all tracked items
- `/remove` - To remove an item from tracking

### How to add an item for tracking:

1. Send the `/add` command
2. The bot will ask you to send a link to the product
3. Copy the product link from the online store's website and send it to the bot
4. The bot will confirm the addition of the product and show the current price.

### How it works:

- The bot will check the prices of all added items every day at 9:00 a.m.
- If the price changes, the bot will send you a notification.
- The notification will show the old price, the new price and the percentage of change.

### How to run a bot all the time (so that it works 24/7):

#### Windows:
1. Create the `start_bot' file.bat` in the same folder with the following contents:
``
   @echo off
echo Launching a price tracking bot...
python price_tracker_bot.py
pause
   ```
2. Run this file instead of the command in the command prompt

#### Linux:
To automatically launch the bot when the system boots, run:
1. Create a service file:
   ```
   sudo nano /etc/systemd/system/price-tracker-bot.service
   ```
2. Add the following contents to it (replace the path with yours):
   ```
   [Unit]
   Description=Price Tracker Telegram Bot
   After=network.target

   [Service]
   User=YOUR_USERNAME
   WorkingDirectory=/home/YOUR_USERNAME/price-tracker-bot
   ExecStart=/usr/bin/python3.9 /home/YOUR_USERNAME/price-tracker-bot/price_tracker_bot.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. Replace YOUR_USERNAME with your user's name
4. Save the file (Ctrl+O, then Enter) and exit (Ctrl+X)
5. Perform:
   ```
   sudo systemctl enable price-tracker-bot.service
   sudo systemctl start price-tracker-bot.service
   ```

## Problem solving

### If the bot does not start:

1. **Check if Python is installed correctly.**
   - On Windows: type `python --version` at the command prompt
   - On Linux: type `python3.9 --version` in the terminal

2. **Check if the libraries are installed correctly.**
   - On Windows: `pip list | findstr telegram`
- On Linux: `pip3 list | grep telegram`

3. **Check the correctness of the token**
- Make sure that the token is inserted correctly, without unnecessary spaces

4. **Check your internet access**
   - The bot requires a constant internet connection

If the bot cannot determine the price on some site, it is possible that the site structure is not supported. In this case, try another store.
