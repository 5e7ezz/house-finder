import datetime
import json
import sqlite3
import time

import requests

# 拉取來自591的房屋
import urllib3
from selenium import webdriver

SOURCE = '591'
DATABASE = './houses.db'
URL = 'https://sale.591.com.tw/home/search/list?type=2&shType=list&regionid={county}&section={district}&price={price}{next}'
NEXT = '&firstRow={first_row}&totalRows={total_rows}'
# Cookie 從瀏覽器上拷貝 591_new_session 這段即可
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
    'Host': 'sale.591.com.tw',
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'DNT': '1',
    'X-CSRF-TOKEN': '',
    'X-Requested-With': 'XMLHttpRequest',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://sale.591.com.tw/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cookie': ''
}

PAGE_COUNT = 5


def get_county_code(county):
    with open('county_591.json', encoding='utf8') as f:
        counties = json.load(f)
        return counties[county] if county in counties else ''


def get_district_code(county, district):
    with open('district_591.json', encoding='utf8') as f:
        districts = json.load(f)
        if county in districts:
            ds = districts[county]
            return ds[district] if district in ds else ''
        else:
            return ''


def init_headers():
    try:
        wait = 60
        options = webdriver.ChromeOptions()
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_argument('--window-position=0,0')
        options.add_argument("--incognito")
        options.add_argument("window-size=1920,1080")
        options.page_load_strategy = 'none'
        driver = webdriver.Chrome(options=options)
        driver.get('https://sale.591.com.tw/')
        driver.set_page_load_timeout(wait)
        driver.implicitly_wait(wait)
        time.sleep(wait)
        now_time = time.strftime('%Y%m%d %H:%M:%S')
        driver.get_screenshot_as_file(
            './screenshots/{time} - list_error.png'.format(time=now_time))
        element = driver.find_element_by_name('csrf-token')
        driver.stop_client()
        csrf_value = element.get_attribute('content')
        HEADERS['X-CSRF-TOKEN'] = csrf_value
        HEADERS['Cookie'] = '591_new_session={}'.format(
            driver.get_cookie('591_new_session')['value'])
        print('[591] csrf_value = {}'.format(csrf_value))
    finally:
        driver.close()


def fetch_houses_from_591(user):
    init_headers()
    county = user['county']
    district = user['district']
    price = user['price_range_591']
    user_name = user['user_name']
    house_ids = set()
    query_ids = 'select id from {user_name} where source = "{source}"'.format(
        user_name=user_name, source=SOURCE)
    db = sqlite3.connect(DATABASE)
    try:
        cursor = db.execute(query_ids)
        for d in cursor.fetchall():
            house_ids.add(d[0])
        cursor.close()
    finally:
        db.close()

    page_index = 0
    total_rows = 0
    houses = []
    db = sqlite3.connect(DATABASE)
    county_code = get_county_code(county)
    if type(district) is str:
        district_code = get_district_code(county, district)
    else:
        district_code = ''
        for d in district:
            district_code += '{},'.format(get_district_code(county, d))
        district_code = district_code[0:-1]
    while page_index < PAGE_COUNT:
        print('[{source}]拉取{county}{district}價位區間{price}第{index}頁資訊'.format(source=SOURCE, county=county, district=district,
                                                                            price=price, index=(page_index + 1)))
        url = URL.format(county=county_code, district=district_code, price=price, timestamp=int(
            datetime.datetime.now().timestamp()), next='')
        if page_index > 0 and total_rows != 0:
            first_row = page_index * 30
            url = URL.format(county=county_code, district=district_code, price=price,
                             timestamp=int(
                                 datetime.datetime.now().timestamp()),
                             next=NEXT.format(first_row=first_row, total_rows=total_rows))
        print(url)
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code == 200:
            data = json.loads(resp.text)['data']
            if page_index == 0:
                total_rows = data['total']
            for h in data['house_list']:
                house = {
                    'id': str(h['houseid']),
                    'title': h['title'],
                    'cover': h['photo_url'],
                    'price': h['price'],
                    'link': 'https://sale.591.com.tw/home/house/detail/2/{id}.html'.format(id=h['houseid']),
                    'age': h['houseage'],
                    'room': h['room'],
                    'floor': h['floor'] if 'floor' in h else '0',
                    'area': h['area'],
                    'source': '591'
                }
                if house['id'] in house_ids:
                    print('[{}] 舊物件，略過 - {} - {}'.format(SOURCE,
                                                         house['title'], house['price']))
                    continue
                elif 'keywords' in user and not any(k in house['title'] for k in user['keywords']):
                    print('[{}] 物件不包含關鍵字，略過 - {}'.format(SOURCE, house['title']))
                    continue
                else:
                    print('[{}] 發現新物件 - {} - {}'.format(SOURCE,
                                                        house['title'], house['price']))
                house_ids.add(house['id'])
                try:
                    insert = 'insert into {user_name} (id, title, price, area, cover, link, room, age, floor, source) values (\'{id}\',\'{title}\',\'{price}\',' \
                             '\'{area}\',' \
                             '\'{cover}\',' \
                             '\'{link}\',\'{room}\',\'{age}\',\'{floor}\', \'{source}\')'.format(user_name=user_name,
                                                                                                 id=house['id'],
                                                                                                 title=house['title'],
                                                                                                 price=house['price'],
                                                                                                 area=house['area'],
                                                                                                 cover=house['cover'],
                                                                                                 link=house['link'],
                                                                                                 room=house['room'],
                                                                                                 age=house['age'],
                                                                                                 floor=house['floor'],
                                                                                                 source=SOURCE)
                    db.execute(insert)
                    db.commit()
                except sqlite3.IntegrityError as e:
                    print('[591] UNIQUE constraint failed - {}'.format(e))
                houses.append(house)
        resp.close()
        page_index = page_index + 1
    db.close()
    return houses
