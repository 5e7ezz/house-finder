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
    'Cookie': 'T591_TOKEN=f0a00265-b816-4385-a102-1474fd0350e4; tw591__privacy_agree=0; _ga=GA1.3.1366232960.1622701815; regionCookieId=3; user_index_role=2; _ga=GA1.4.1366232960.1622701815; _fbp=fb.2.1622702478156.768210220; user_browse_recent=a%3A5%3A%7Bi%3A0%3Ba%3A2%3A%7Bs%3A4%3A%22type%22%3Bi%3A2%3Bs%3A7%3A%22post_id%22%3Bi%3A9624409%3B%7Di%3A1%3Ba%3A2%3A%7Bs%3A4%3A%22type%22%3Bi%3A8%3Bs%3A7%3A%22post_id%22%3Bi%3A121805%3B%7Di%3A2%3Ba%3A2%3A%7Bs%3A4%3A%22type%22%3Bi%3A8%3Bs%3A7%3A%22post_id%22%3Bi%3A122124%3B%7Di%3A3%3Ba%3A2%3A%7Bs%3A4%3A%22type%22%3Bi%3A8%3Bs%3A7%3A%22post_id%22%3Bi%3A125583%3B%7Di%3A4%3Ba%3A2%3A%7Bs%3A4%3A%22type%22%3Bi%3A8%3Bs%3A7%3A%22post_id%22%3Bi%3A120318%3B%7D%7D; _fbc=fb.2.1627217686739.IwAR3a4jGZWwq2v6jJ_nplCysFEgRS46FdCeKXapXtr1r1YHr0spTKrjKvnuo; webp=1; PHPSESSID=b4pc0cd74o7t70bugj6rc5jb11; bid[pc][114.32.179.6]=3228; is_new_index=1; is_new_index_redirect=1; urlJumpIp=3; index_keyword_search_analysis=%7B%22role%22%3A%222%22%2C%22type%22%3A%221%22%2C%22keyword%22%3A%22%22%2C%22selectKeyword%22%3A%22%E4%B8%89%E9%87%8D%E5%8D%80%22%2C%22menu%22%3A%22%22%2C%22hasHistory%22%3A1%2C%22hasPrompt%22%3A0%2C%22history%22%3A0%7D; newUI=1; urlJumpIpByTxt=%E6%96%B0%E5%8C%97%E5%B8%82; new_rent_list_kind_test=0; XSRF-TOKEN=eyJpdiI6IlNUSENMRENRbWV1WlhCSDdiZWJJa1E9PSIsInZhbHVlIjoiZUpabUVLY2lWRFBJUkx2MTBWRDVNbUZYaytTSmhDMmlWMjhTRUJiVjNGaVNXMmRoUmhLWmN5TEQ4TEJYTXdGejRTNU1RUm9kTHN4dHpVdnhRZkZxOVE9PSIsIm1hYyI6IjViMTQ5NThmOTQ0MGJlZGIxZTljYzk0NDc4M2M4MmRjODVmMmZkNTcwMWJhZjViMzk0ZWRhODgxNDc3NDA1Y2UifQ%3D%3D; 591_new_session=eyJpdiI6InNpUmpDTGpoNE9lXC90YlwvSWlUTXg4Zz09IiwidmFsdWUiOiJ2UnNYOHVsZnJXXC9GVzdER1BjSmlXYTM3RVJJM2dcLzkxSHg4VFwvbXpIUXFvbWQwZUNPWHI1TEdjMFlTV0ZVeFFSVDNOQndLdnlyQmdNXC9cL1wvTFNOdmNEQT09IiwibWFjIjoiYjk3NDgyOGNjMmE2YTNkYzQ4Y2Q2N2M4NGE5MjliYTlkYzUzOWRmMDQ3NmNkZGFmOTNiMWY1ODRmYTRlMWQ0OSJ9'
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
        time.sleep(5)
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
        driver.close
    except Exception as e:
        HEADERS['X-CSRF-TOKEN'] = ""
        HEADERS['Cookie'] = ""


def fetch_houses_from_591(user):
    if HEADERS['X-CSRF-TOKEN'] == "":
        print('[591] HEADER 獲取失敗，結束任務')
        return
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
