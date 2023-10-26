import logging
import urllib.parse
import requests
import time
import psutil
import traceback
from datetime import datetime

from src.config import Config
from src.market import MarketAPI, MarketBuyError, MarketItem
from src.market.api import parse_search_data

DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1251512313/AQUA_dMETqLe5XVZCnn8X"  # Replace this with your actual Discord webhook URL

DISCORD_MESSAGE_SUCCESS = (
    '🎊 Successfully purchased the account: [link](https://lzt.market/{item_id})\n'
    "💲 Price: `{price}₽`\n"
    '👷 Seller: [link](https://zelenka.guru/members/{seller_id}) `{seller_username}`\n'
    '⏱️ Time Taken: {time_taken} ms\n'
    '📅 Date and Time: {current_time}\n'
    '🔢 Total Accounts Purchased: {total_purchased}\n'
    '💳 Payment Method: {payment_method}\n'
    '🔗 Search URL: [link](https://lzt.market/search/{search_url})\n'
    '@everyone'
)

DISCORD_MESSAGE_FAILURE = (
    '❗ Failed to purchase the account: [link](https://lzt.market/{item_id})\n'
    "💲 Price: `{price}₽`\n"
    '👷 Seller: [link](https://zelenka.guru/members/{seller_id}) `{seller_username}`\n'
    '❌ Error Message: {error_message}\n'
    '📅 Date and Time: {current_time}\n'
    '🔢 Total Accounts Purchased: {total_purchased}\n'
    '💳 Payment Method: {payment_method}\n'
    '🔗 Search URL: [link](https://lzt.market/search/{search_url})\n'
    '@everyone'
)

DISCORD_MESSAGE_STARTUP = (
    '🤖 Bot has started!\n'
    '⏰ Current Time: {current_time}\n'
    '🖥️ System Info:\n'
    '    CPU Usage: {cpu_usage}%\n'
    '    Memory Usage: {memory_usage}%\n'
    '    Disk Usage: {disk_usage}%\n'
    '🔧 Configuration File: {config_file}\n'
    '🔢 Total Searches to Perform: {total_searches}\n'
    '🔢 Total Accounts to Purchase: {total_accounts}\n'
    '💳 Payment Method: {payment_method}\n'
    '🔗 Search URLs:\n{search_urls}\n'
    '@everyone'
)

DISCORD_MESSAGE_SEARCH_COUNT = (
    '🔍 Total searches performed: {count_searches}\n'
    '⏰ Current Time: {current_time}\n'
    '🖥️ System Info:\n'
    '    CPU Usage: {cpu_usage}%\n'
    '    Memory Usage: {memory_usage}%\n'
    '    Disk Usage: {disk_usage}%\n'
    '@everyone'
)

def send_discord_message(message):
    payload = {"content": message, "parse_mode": "none"}
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

def get_system_info():
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    return cpu_usage, memory_usage, disk_usage

def send_crash_message(error_message, config_file, total_searches, total_accounts, payment_method, search_urls):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    discord_message_crash = (
        f'🚨 Bot has crashed!\n'
        f'⏰ Crash Time: {current_time}\n'
        f'❌ Error Message: {error_message}\n'
        f'📋 Traceback:\n```{traceback.format_exc()}```\n'
        f'🖥️ System Info:\n'
        f'    CPU Usage: {psutil.cpu_percent()}%\n'
        f'    Memory Usage: {psutil.virtual_memory().percent}%\n'
        f'    Disk Usage: {psutil.disk_usage("/").percent}%\n'
        f'🔧 Configuration File: {config_file}\n'
        f'🔢 Total Searches to Perform: {total_searches}\n'
        f'🔢 Total Accounts to Purchase: {total_accounts}\n'
        f'💳 Payment Method: {payment_method}\n'
        f'🔗 Search URLs:\n{search_urls}\n'
        f'@everyone'
    )
    send_discord_message(discord_message_crash)


def main(searches):
    config = Config.load_config("configuration.ini")
    logging.basicConfig(
        level=config.logging.level,
        format=config.logging.format,
    )
    lolzteam_token = config.lolzteam.token
    count_purchase = 0
    count_searches = 0  # Counter for total searches
    failed_purchase_attempts = []  # List to store item IDs with failed purchase attempts

    cpu_usage, memory_usage, disk_usage = get_system_info()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    discord_message_startup = DISCORD_MESSAGE_STARTUP.format(
        current_time=current_time,
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        disk_usage=disk_usage,
        config_file="configuration.ini",
        total_searches=len(searches),
        total_accounts=config.lolzteam.count,
        payment_method=config.lolzteam.payment_method,
        search_urls="\n".join(config.lolzteam.search_urls_list),
    )
    send_discord_message(discord_message_startup)
    time.sleep(10)  # Delay for 10 seconds

    try:
        market = MarketAPI(lolzteam_token)
        while True:  # Loop forever
            for search, params in searches:
                count_searches += 1  # Increment the total searches counter
                if count_searches % 10000 == 0:  # Check if 10000 searches have been performed
                    send_search_count_message(count_searches)

                search_result = market.search(search, params)
                items = search_result.get("items", [])

                logging.info(
                    "%s Accounts found by query with parameters %s %s",
                    search,
                    urllib.parse.unquote(params),
                    len(items),
                )

                for item in items:
                    item_id = item["item_id"]
                    
                    # Skip the item if it has already failed a purchase attempt
                    if item_id in failed_purchase_attempts:
                        continue

                    market_item = MarketItem(item, lolzteam_token)
                    try:
                        logging.info("Purchasing an account %s", item_id)
                        start_time = time.time()  # Start time before making the purchase request
                        market_item.fast_buy()
                        end_time = time.time()  # End time after the purchase request completes
                        time_taken = round((end_time - start_time) * 1000, 2)  # Calculate time taken in milliseconds
                    except MarketBuyError as error:
                        logging.warning(
                            " When trying to buy an account %s An error has occurred: %s",
                            item_id,
                            error.message,
                        )

                        # Add the item to the failed_purchase_attempts list
                        failed_purchase_attempts.append(item_id)

                        discord_message_failure = DISCORD_MESSAGE_FAILURE.format(
                            item_id=item_id,
                            price=market_item.item_object["price"],
                            seller_id=market_item.item_object["seller"]["user_id"],
                            seller_username=market_item.item_object["seller"]["username"],
                            error_message=error.message,
                            current_time=current_time,
                            total_purchased=count_purchase,
                            thumbnail=market_item.item_object.get("thumbnail_url", "N/A"),
                            payment_method=market_item.item_object.get("payment_method", "Unknown Payment Method"),
                            search_url=urllib.parse.quote(params),
                        )
                        send_discord_message(discord_message_failure)
                        continue
                    else:
                        logging.info("Account %s successfully purchased!", item_id)
                        count_purchase += 1

                        account_object = market_item.item_object
                        seller = account_object["seller"]

                        discord_message_success = DISCORD_MESSAGE_SUCCESS.format(
                            item_id=item_id,
                            price=account_object["price"],
                            seller_id=seller["user_id"],
                            seller_username=seller["username"],
                            time_taken=time_taken,
                            current_time=current_time,
                            total_purchased=count_purchase,
                            thumbnail=account_object.get("thumbnail_url", "N/A"),
                            payment_method=account_object.get("payment_method", "Unknown Payment Method"),
                            search_url=urllib.parse.quote(params),
                        )
                        send_discord_message(discord_message_success)

                        if count_purchase >= config.lolzteam.count:
                            logging.info(
                                "Successfully purchased %s accounts. Job completed.",
                                count_purchase,
                            )
                            exit()
                        break


    except Exception as e:
        error_message = str(e)
        search_urls_str = "\n".join(config.lolzteam.search_urls_list)
        send_crash_message(
            error_message,
            "configuration.ini",
            len(searches),
            config.lolzteam.count,
            config.lolzteam.payment_method,
            search_urls_str,
        )
        raise

def send_search_count_message(count_searches):
    cpu_usage, memory_usage, disk_usage = get_system_info()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = DISCORD_MESSAGE_SEARCH_COUNT.format(
        count_searches=count_searches,
        current_time=current_time,
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        disk_usage=disk_usage,
    )
    send_discord_message(message)

if __name__ == "__main__":
    searches = []  # Define searches globally
    config = Config.load_config("configuration.ini")  # Move this line here
    for search_url in config.lolzteam.search_urls_list:
        category, params = parse_search_data(search_url)
        searches.append((category, params))

    while True:  # Loop forever
        try:
            main(searches)  # Pass the searches variable to the main function
        except Exception as e:
            logging.exception("An error occurred during the main loop: %s", e)
            time.sleep(60)  # Add a delay to prevent excessive error logging and to wait before the next attempt
