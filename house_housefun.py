import json
import sqlite3
import time
from urllib.parse import quote

from selenium import webdriver
from selenium.common.exceptions import TimeoutException

DATABASE = './houses.db'
SOURCE = '好房網'
URL = 'https://buy.housefun.com.tw/region/{county}-{district}_c/{price}_price/?pg={index}'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'


def fetch_houses_from_network(user):
    """
    :return: list of houses
    """
    # 先把舊物件的 id 從資料庫拉出來，等一下用來快速判斷是否是新物件
    county = user['county']
    district = user['district']
    price_range = user['price_range']
    user_name = user['user_name']
    house_ids = set()
    houses = []
    query_ids = 'select id from {user_name} where source = "{source}"'.format(user_name=user_name, source=SOURCE)
    db = sqlite3.connect(DATABASE)
    try:
        cursor = db.execute(query_ids)
        for d in cursor.fetchall():
            house_ids.add(d[0])
        cursor.close()
    finally:
        db.close()

    # 從網路上拉物件，如果 id 表為空代表是第一次拉取，就拉多一點資料
    driver = None
    count = 5 if len(house_ids) == 0 else 3
    for i in range(count):
        print('[{source}] 拉取{county}{district}價位區間{price}第{index}頁資訊'.format(source=SOURCE, county=county, district=district,
                                                                             price=price_range, index=(i + 1)))
        url = URL.format(county=quote(county), district=quote(district), price=price_range, index=(i + 1))
        retry_count = 0
        wait_time = 60
        while retry_count < 3:
            try:
                if driver:
                    print('[好房網] 結束上次連線')
                    driver.quit()
                if retry_count != 0:
                    print('[好房網] 重試第{}次'.format(retry_count))
                wait_time = wait_time + retry_count * 10
                options = webdriver.ChromeOptions()
                options.add_argument('--blink-settings=imagesEnabled=false')
                options.add_argument('--window-position=4000,0')
                options.add_argument("--incognito")
                options.add_argument("user-agent={}".format(USER_AGENT))
                driver = webdriver.Chrome(options=options)
                driver.maximize_window()
                driver.delete_all_cookies()
                driver.get(url)
                driver.set_page_load_timeout(wait_time)
                driver.implicitly_wait(wait_time)
                time.sleep(wait_time)
                if not driver.page_source:
                    print('[好房網] no page_source')
                    retry_count = retry_count + 1
                    now_time = time.strftime('%Y%m%d %H:%M:%S')
                    driver.get_screenshot_as_file('./screenshots/{time} - list_error.png'.format(time=now_time))
                    driver.close()
                    continue
                elements = driver.find_elements_by_xpath('/html/head/script[22]')
                if not elements or len(elements) == 0:
                    print('[好房網] no element')
                    retry_count = retry_count + 1
                    now_time = time.strftime('%Y%m%d %H:%M:%S')
                    driver.get_screenshot_as_file('./screenshots/{time} - list_error.png'.format(time=now_time))
                    driver.close()
                    continue
                element = elements[0]
                content = element.get_attribute('innerHTML').strip().replace('@', '')
                data = json.loads(content)['graph']
                try:
                    for d in data:
                        if d['type'] == 'Product':
                            house_id = d['productID']
                            title = d['name']
                            cover = 'https:{}'.format(d['image'])
                            price = int(d['offers']['price']) / 10000
                            link = d['offers']['url']
                            house = {
                                'id': house_id,
                                'title': title,
                                'cover': cover,
                                'price': price,
                                'link': link,
                                'age': 0,
                                'room': 0,
                                'floor': 0,
                                'area': 0,
                                'source': SOURCE
                            }
                            if house_id in house_ids:
                                if house['id'] in house_ids:
                                    print('[{}] 舊物件，略過 - {}'.format(SOURCE, house['title']))
                                continue
                            else:
                                print('[{}] 發現新物件 - {}'.format(SOURCE, house['title']))

                            houses.append(house)
                            if len(houses) > 10:
                                print('[好房網] 物件太多，先顯示前{num}筆物件'.format(num=len(houses)))
                                driver.quit()
                                return houses
                except ValueError as e:
                    print('[好房網] ValueError - {}'.format(e))
                break
            except ValueError as e:
                print('[好房網] ValueError - {}'.format(e))
            except IndexError as e:
                print('[好房網] IndexError - {}'.format(e))
            except TimeoutException as e:
                print('[好房網] TimeoutException - {}'.format(e))
            finally:
                time.sleep(5)
        driver.quit()

    print('found {num} houses'.format(num=len(houses)))
    return houses


def fetch_houses_detail_data(houses, user_name):
    """
    給定粗略的物件列表，針對每個物件去求取詳細資料，並於抓取詳細資料後，將資料寫回資料庫
    :param houses: 物件列表
    :return: 物件詳細資料列表
    """
    new_houses = []
    if len(houses) == 0:
        print('[好房網] 沒有物件需要解析')
        return new_houses
    database = sqlite3.connect(DATABASE)

    driver = None
    for house in houses:
        retry_count = 0
        wait_time = 300
        while retry_count < 3:
            try:
                wait_time += retry_count * 10
                if driver:
                    print('[好房網] 結束上次連線')
                    driver.quit()
                if retry_count == 0:
                    print('[好房網] 準備解析物件 - {}'.format(house['title']))
                else:
                    print('[好房網] 重試第{}次 - {}'.format(retry_count + 1, house['title']))
                options = webdriver.ChromeOptions()
                options.add_argument('--blink-settings=imagesEnabled=false')
                options.add_argument('--window-position=4000,0')
                options.add_argument("--incognito")
                options.add_argument("user-agent={}".format(USER_AGENT))
                # options.add_experimental_option("debuggerAddress", "localhost:9222")
                driver = webdriver.Chrome(options=options)
                driver.maximize_window()
                driver.delete_all_cookies()
                driver.get(house['link'])
                driver.set_page_load_timeout(wait_time)
                driver.implicitly_wait(wait_time)
                time.sleep(wait_time)
                if not driver.page_source:
                    retry_count += 1
                    continue
                elements = driver.find_elements_by_xpath('/html/head/script[24]')
                if not elements or len(elements) == 0:
                    retry_count += 1
                    now_time = time.strftime('%Y%m%d %H:%M:%S')
                    driver.get_screenshot_as_file('./screenshots/{time} - {title}.png'.format(time=now_time, title=house['title']))
                    continue
                element = elements[0]
                content = element.get_attribute('innerHTML').strip()
                index = content.index('var ltm_data = ')
                content = content[index + len('var ltm_data = '):-1]
                detail = json.loads(content)['pagedata']['house_data']
                house['age'] = detail['age']
                house['room'] = detail['room']
                house['area'] = detail['ping']
                house['floor'] = detail['floor']
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
                database.execute(insert)
                database.commit()
                new_houses.append(house)
                print('[好房網] 完成解析物件 - {}'.format(house['title']))
                break
            except ValueError as e:
                print('[好房網] ValueError - {}'.format(e))
                retry_count += 1
            except IndexError as e:
                print('[好房網] IndexError - {}'.format(e))
                retry_count += 1
            except TimeoutException as e:
                print('[好房網] TimeoutException - {}'.format(e))
                retry_count += 1
    driver.close()
    driver.quit()
    database.close()
    print('len(new_houses) = {}'.format(len(new_houses)))
    return new_houses
