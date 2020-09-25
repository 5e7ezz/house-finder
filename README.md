# house-finder
## 功能說明
好房網物件訊息推送至 telegram

## 獲取 telegram chat id

- 執行 telegram_bot.py
- 於 telegram 上，將 my_house_finder_bot 加入好友
- 對 my_house_finder_bot 說 /start
- 從 telegram_bot.py 的 console 中獲得 chat id

## 新增使用者

- 將獲取到的 chat_id 增添至 houses.py 內
- 除了 chat_id，還需要填寫地區與價格區間
- 定期執行 houses.py 即可獲得最新房屋物件資訊

## 問題排除

### 如何在 terminal 環境下運行
- 確認環境中已有 chrome
- 安裝 xvfb


## 參考文件

- https://github.com/python-telegram-bot/python-telegram-bot/wiki/Transition-guide-to-Version-12.0
- https://github.com/python-telegram-bot/python-telegram-bot/tree/master/examples





