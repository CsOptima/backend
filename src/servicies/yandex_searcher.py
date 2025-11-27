from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import urllib.parse


class YandexSearcher:
    WAIT_TIME = 7

    @classmethod
    def extract_urls(cls, text):
        url_pattern = r'[\w\-\.]+\.[a-z]{2,}(?:[\w\-\.,@?^=%&:\/~\+#]*[\w\-\@?^=%&\/~\+#])?'

        urls = re.findall(url_pattern, text)

        return '\n'.join(set(urls))

    @classmethod
    def search_yandex_neuro(cls, query):
        # Настройки браузера
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless") # Раскомментируйте для скрытого режима
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        try:
            # 1. Формируем параметры запроса
            params = {
                "text": query,
                "promo": "force_neuro",  # <--- Тот самый параметр
            }

            # Превращаем словарь в строку: ?text=...&promo=force_neuro&lr=213
            query_string = urllib.parse.urlencode(params)

            # Собираем полный URL
            target_url = f"https://yandex.ru/search/?{query_string}"

            print(f"🔗 Переход по ссылке: {target_url}")

            # 2. Переходим сразу на страницу выдачи
            driver.get(target_url)

            # Ждем загрузки (для Нейро-режима иногда нужно чуть больше времени, чтобы JS отработал)
            time.sleep(cls.WAIT_TIME)

            # 3. Парсинг (логика та же, но учтите, что Нейро-выдача может сдвинуть обычные результаты)
            gpt_answer = driver.find_element(By.CSS_SELECTOR, ".FuturisGPTMessage")

            return gpt_answer.text

        except Exception as e:
            print(f"Ошибка: {e}")
            return []
        finally:
            driver.quit()

# print(search_yandex_neuro("Нииэт"))
