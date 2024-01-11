import requests, time
from bs4 import BeautifulSoup
#import pandas as pd
from typing import Final
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--enable-strict-powerful-feature-restrictions")
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
#options.add_argument('--enable-javascript')
options.add_argument("--disable-geolocation")
#options.add_argument("start-maximized")
options.add_argument(f"--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36")
options.add_argument("--headless")
options.add_experimental_option('excludeSwitches', ['enable-automation'])
driver = webdriver.Chrome(service=service, options=options)
TOKEN = None
BASE_URL = 'https://goldapple.ru'
BOT_USERNAME: Final = '@ppricechecker_bot'
TELEGRAM_API_SEND_MESSAGE = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
# aroma group used in sorting, resionous (10) is set by default
AROMA_GROUP = 10
with open("token.txt") as f:
    TOKEN = f.read().strip()
# getting the links list with the selected parameters
def get_links(AROMA_GROUP):
    productlinks = []
    pages = 1
    x = 1
    while x <= pages:
        driver.get(f'https://goldapple.ru/parfjumerija/zhenskie-aromaty-parfume?p={x}&storestocks=1&top={AROMA_GROUP}')
        time.sleep(5)
        items_count = driver.find_element(By.XPATH, "//span[@class='HZo7s']").text
        res = [int(i) for i in items_count.split() if i.isdigit()]
        res_int = int(''.join(map(str, res)))
        pages = (res_int // 24)

        # работаем с BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        productlist = soup.find_all("article",{"itemtype":"https://schema.org/Product"})
        for product in productlist:
            link = product.find("a").get("href")
            productlinks.append(BASE_URL + link)
        x += 1
    print("Всего позиций по запросу:", len(productlinks))
    return productlinks

# printing results
def results(productlinks):
    for product in productlinks:
        driver.get(product)
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        product_name = driver.find_element(By.XPATH, "//div[@class='_8bkoV']").text
        product_price = driver.find_element(By.XPATH, "//meta[@itemprop='price']").get_attribute("content")
        #product_volume = driver.find_element(By.XPATH, "//div[contains(@class, 'VqOtl') and contains (@class, 'C7gtk')]").text
        product_test = soup.select('dt.U7pco') 
        print(product_name, product_price + "₽")
        print("Верхние ноты:", product_test[3].text)
        print("Средние ноты:", product_test[4].text)
        print("Базовые ноты:", product_test[5].text)
        print("Ссылка:", product)
        return [product_name, product_price, product_test[3].text, product_test[4].text, product_test[5].text, product]

# TELEGRAM PART BEGINS HERE

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Введи номер группы ароматов (10 — смолистые, 16 — табачные):')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('I can help you')

async def something_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Do a barrel roll!')

# Responses

def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    # Process the user input (Replace this with your actual processing logic)
    processed_values = results(get_links(int(user_input)))

    # Format the processed values into a message
    message = format_message(processed_values)

    # Send the formatted message back to the user
    update.message.reply_text(message)

def format_message(processed_values):
    # Format the processed values into a pretty message
    message = f"{processed_values[0]}\n"
    message += f"{processed_values[1]}₽\n"
    message += f"Верхние ноты: {processed_values[2]}\n"
    message += f"Средние ноты: {processed_values[3]}\n"
    message += f"Базовые ноты: {processed_values[4]}\n"
    message += f"Ссылка: {processed_values[5]}\n"

    return message


def handle_response(text: str) -> str:
    processed: str = text.lower()

    if '10' in processed:
        return format_message(results(get_links(int(10))))
    if '16' in processed:
        return format_message(results(get_links(int(16))))
    if 'what\'s up?' in processed:
        return 'Ye i\'m good!'
    return 'I don\'t understand you...'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User {update.message.chat.id} in {message_type} : "{text}"')

    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)

    print('Bot:', response)
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('something', something_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)