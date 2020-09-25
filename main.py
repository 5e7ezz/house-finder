import os
import platform
import signal
import sqlite3
import time
from datetime import datetime

import psutil
import requests
import telegram
from telegram import TelegramError

import house_591
import house_housefun

TELEGRAM_BOT_NAME = 'my_house_finder_bot'
TELEGRAM_BOT_TOKEN = '1162799956:AAEjxUJ3mVP7QD9B4VflfC33T3HGh-ZI4NI'
ADMIN_LINE_ID = 'AooktNKFxH7mPGSRSXGUj5tmf2KWpvVndXjxjQQa0xl'
DATABASE = './houses.db'
USERS = [
    {
        'user_name': 'lili',
        'county': '新北市',
        'district': '三重區',
        'price_range': '800-1000',
        'price_range_591': '800$_1000$',
        'telegram_chat_id': [],
        'line_chat_id': ['MiJ2KmO0VPEB4UOWn2ocjIL1xom87lYxDTGfUKFKkeU '],
    }
    , {
        'user_name': 'jessie',
        'county': '新北市',
        'district': '蘆洲區',
        'price_range': '1500-2800',
        'price_range_591': '1500$_2800$',
        'telegram_chat_id': [],
        'line_chat_id': ['GqQIIW1Bfvrxtv6vVuzszNlkk47LFdycS3dT872Cni2'],
    }
    , {
        'user_name': 'kevin',
        'county': '新北市',
        'district': '林口區',
        'price_range': '-1000',
        'price_range_591': '_1000$',
        'telegram_chat_id': [765968974],
        'line_chat_id': [],
        'keywords': ['租', '套']
    }
    , {
        'user_name': 'james',
        'county': '新北市',
        'district': '三重區',
        'price_range': '-1000',
        'price_range_591': '_1000$',
        'telegram_chat_id': [549970579],
        'line_chat_id': ['AooktNKFxH7mPGSRSXGUj5tmf2KWpvVndXjxjQQa0xl'],
        'keywords': ['租', '套']
    }
    , {
        'user_name': 'james',
        'county': '新北市',
        'district': '三重區',
        'price_range': '800-2000',
        'price_range_591': '1000$_2000$',
        'telegram_chat_id': [549970579, 1133348584],
        'line_chat_id': ['AooktNKFxH7mPGSRSXGUj5tmf2KWpvVndXjxjQQa0xl']
    }
    , {
        'user_name': 'michael',
        'county': '新北市',
        'district': '新店區',
        'price_range': '1000-1500',
        'price_range_591': '1000$_1500$',
        'telegram_chat_id': [623417355],
        'line_chat_id': ['wCsapOjDxtXrImCLvgJYBCAimB0rLShFC1B0eq6p0rC']
    }
    , {
        'user_name': 'frank',
        'county': '台北市',
        'district': '大同區',
        'price_range': '800-2000',
        'price_range_591': '1000$_2000$',
        'telegram_chat_id': [945978483],
        'line_chat_id': list()
    }
    , {
        'user_name': 'charles',
        'county': '台北市',
        'district': '文山區',
        'price_range': '800-2000',
        'price_range_591': '800$_2000$',
        'telegram_chat_id': [849506711],
        'line_chat_id': ['8w6KfBvujvuwLYvv9eQNMfZs56rTkNIu9DFUDKXqJSr']
    }
     ,{
        'user_name': 'fiona',
        'county': '台北市',
        'district': ['萬華區', '中山區', '中正區', '大同區'],
        'price_range': '2000-3500',
        'price_range_591': '2000$_3500$',
        'telegram_chat_id': [],
        'line_chat_id': ['ChNOb9SdMFFAzmOPgBCvXpMpwMOvnFKoHlI0EpDpaHr']
    }
    , {
        'user_name': 'fiona',
        'county': '新北市',
        'district': '板橋區',
        'price_range': '2000-3000',
        'price_range_591': '2000$_3000$',
        'telegram_chat_id': [],
        'line_chat_id': ['ChNOb9SdMFFAzmOPgBCvXpMpwMOvnFKoHlI0EpDpaHr']
    }
]


def check_table_exist(table_name):
    """
    檢查特定表名是否存在
    :param table_name: e.g. houses_james
    :return: 是否
    """
    db = sqlite3.connect(DATABASE)
    query_table_name = 'select count(name) from sqlite_master where type = "table" and name = "{table_name}"'.format(
        table_name=table_name)
    result = db.execute(query_table_name).fetchone()[0] == 1
    db.close()
    return result


def create_table_for_user(user_name):
    """
    建立使用者對應的表名
    :param user_name: e.g. houses_james
    """
    try:
        db = sqlite3.connect(DATABASE)
        create = '''CREATE TABLE {user_name}
                           (id TEXT PRIMARY KEY     NOT NULL,
                           title            TEXT    NOT NULL,
                           price            TEXT,
                           area             TEXT,
                           cover            TEXT,
                           link             TEXT,
                           room             TEXT,
                           age              TEXT,
                           floor            TEXT,
                           source           TEXT);'''.format(user_name=user_name)
        db.execute(create)
        db.commit()
        db.close()
    finally:
        print('done')


def send_house_to_telegram_user(bot, user_id, house):
    """
        將一件房屋資訊推送給使用者 by telegram
        :param bot: Telegram.Bot(TOKEN)
        :param user_id: line notify token
        :param house: 物件資訊
        :return: None
        """
    if not user_id or not house:
        return None
    time.sleep(5)
    try:
        bot.send_photo(chat_id=user_id,
                       photo=house['cover'],
                       caption='{title} - {price}萬 - {area}坪'.format(title=house['title'], price=house['price'],
                                                                     area=house['area']),
                       disable_notification=True,
                       timeout=120,
                       reply_markup=telegram.InlineKeyboardMarkup(
                           inline_keyboard=[[telegram.InlineKeyboardButton(text=u'點我看詳情', url=house['link'])]]))
    except TelegramError as e:
        print('link = {}'.format(house['link']))
        print('TelegramError - {}'.format(e))


def send_houses_to_telegram_user(user_id, houses):
    """
    將房屋資訊推送給使用者 by telegram
    :param user_id: line notify token
    :param houses: 物件資訊 list
    :return:
    """
    print('準備推送資訊')
    if houses is None or len(houses) == 0:
        print('[telegram]沒有新物件可推送，結束')
        return
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    total = len(houses)
    progress = 1
    for house in houses:
        print('[telegram]推送物件 {}/{} - {}'.format(progress, total, house['title']))
        progress += 1
        send_house_to_telegram_user(bot, user_id, house)


def send_house_to_line_user(user_id, house):
    """
    將一個房屋資訊推送給使用者 by line notify
    :param user_id: line notify token
    :param house: 單個物件的資訊
    :return:
    """
    if not user_id or not house:
        return None
    time.sleep(2)
    url = 'https://notify-api.line.me/api/notify'
    headers = {
        "Authorization": "Bearer " + user_id,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    print(house)
    msg = '[{source}]{title} - {price}萬 - {area}坪\n{link}'.format(
        source=house['source'] if 'source' in house else ''
        , title=house['title']
        , price=house['price']
        , area=house['area']
        , link=house['link'])

    payload = {
        'message': msg,
        'imageThumbnail': house['cover'],
        'imageFullsize': house['cover']
    }

    response = requests.post(url, headers=headers, data=payload)
    return response


def send_msg_to_user(user_id, msg):
    if not user_id or not msg:
        return None
    url = 'https://notify-api.line.me/api/notify'
    headers = {
        "Authorization": "Bearer " + user_id,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {
        'message': msg,
    }

    response = requests.post(url, headers=headers, data=payload)
    return response


def send_houses_to_line_user(user_id, houses):
    """
    將房屋資訊推送給使用者 by line notify
    :param user_id: line notify token
    :param houses: houses data
    :return: None
    """
    if not houses:
        return
    if len(houses) == 0:
        print('[LINE]沒有物件需要推送 - 結束推送任務')
        return

    total = len(houses)
    progress = 1
    for house in houses:
        response = send_house_to_line_user(user_id, house)
        print('[LINE]推送第{}/{}筆資料 - {}'.format(progress, total, response.status_code if response else 'Error'))
        progress += 1


def main():
    """
    主程序進入點
    """
    start_time = datetime.now()
    for user in USERS:
        user_name = user['user_name']
        if not check_table_exist(user_name):
            create_table_for_user(user_name)
        county = user['county']
        district = user['district']
        price_range = user['price_range']
        print('[INFO] 處理 {} - {} - {} - {}'.format(user_name, county, district, price_range))
        houses_detail = []
        print('[591] START - {}'.format(user_name))
        houses_detail.extend(house_591.fetch_houses_from_591(user))
        for telegram_id in user['telegram_chat_id']:
            send_houses_to_telegram_user(telegram_id, houses_detail)
        for line_id in user['line_chat_id']:
            send_houses_to_line_user(line_id, houses_detail)

    # for user in USERS:
    #     houses_detail = []
    #     start_time = datetime.now()
    #     try:
    #         print('[好房網] STEP#1 - {}'.format(user_name))
    #         houses = house_housefun.fetch_houses_from_network(user)
    #         if houses:
    #             print('[好房網] STEP#2 - {}'.format(user_name))
    #             if 'keywords' in user:
    #                 houses = [house for house in houses if any(k in house['title'] for k in user['keywords'])]
    #             houses_detail.extend(house_housefun.fetch_houses_detail_data(houses, user_name))
    #             for telegram_id in user['telegram_chat_id']:
    #                 send_houses_to_telegram_user(telegram_id, houses_detail)
    #             for line_id in user['line_chat_id']:
    #                 send_houses_to_line_user(line_id, houses_detail)
    #     except Exception as e:
    #         print(e)
    #     time.sleep(60)

    send_msg_to_user(ADMIN_LINE_ID, '任務結束')


def finish():
    for process in psutil.process_iter():
        try:
            process_name = process.name()
            process_id = process.pid
            if 'chrome' in process_name or 'Xvfb' in process_name or 'chromedriver' in process_name:
                print('{}'.format(process_name))
                os.kill(process_id, signal.SIGKILL)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            os.passprint(platform.system())


if __name__ == '__main__':
    if platform.system() == 'Linux':
        from xvfbwrapper import Xvfb

        with Xvfb(width=1920, height=1080, colordepth=16) as xvfb:
            xvfb.start()
            main()
        finish()
    else:
        main()
