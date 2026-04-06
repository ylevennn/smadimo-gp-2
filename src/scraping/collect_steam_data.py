from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd

# https://thecode.media/python-timing/ - для замера времени получения игры
import time

from pathlib import Path
import sys

root_path = Path(__file__).resolve().parents[2]
sys.path.append(str(root_path))
from src.logs.logger import logger

log = logger()

try:
    indie_games = pd.read_excel(root_path / 'data' / 'indie_games.xlsx')
    games_ids = indie_games['steam_app_id'].to_list()
    games_data = []
except Exception as e:
    log.error(f'Ошибка при получении id игр | Exception: {e}')
    exit()

game_page_base_url = 'https://store.steampowered.com/app/'
try:
    driver = webdriver.Chrome()
except Exception as e:
    log.error(f'Ошибка при запуске Chrome webdriver | Exception: {e}')
    exit()

# обязательный ввод желаемого среза для парсинга: для разбиения процесса
attempts = 0
while attempts <= 5:
    selected_slice = input('Введите желаемый срез датасета инди игр в формате: 0, 1000 (для случая [0:1000])').split(',')
    try:
        selected_games_ids = games_ids[int(selected_slice[0]):int(selected_slice[1])]
        break
    except:
        print('Неверный формат ввода среза')
        attempts += 1
        if attempts == 5:
            exit()

total_start = time.perf_counter() # старт замера времени для всех игр

for game_id in selected_games_ids:
    start = time.perf_counter()
    game_page_url = game_page_base_url + str(game_id) + '/'

    try:
        driver.get(game_page_url)
    except Exception as e:
        log.error(f'Ошибка при открытии страницы {game_page_url} | steam_id = {game_id} | Exception: {e}')
        continue

    # Страница с проверкой на возраст: выбрать нужный возраст и открыть страницу с игрой
    try:
        select_birthday_date = driver.find_element(by=By.CLASS_NAME, value='agegate_birthday_desc')

        try:
            select_year = Select(driver.find_element(by=By.NAME, value='ageYear'))
            select_year.select_by_value('2000')
        except Exception as e:
            log.error(f'Ошибка при выборе года рождения для игры {game_page_url} | steam_id = {game_id} | Exception: {e}')
            continue

        try:
            open_game_page_button = driver.find_element(by=By.ID, value='view_product_page_btn')
            open_game_page_button.click()
        except Exception as e:
            log.error(f'Ошибка при открытии страницы игры после выбора даты рождения: {game_page_url} | steam_id = {game_id} | Exception: {e}')
            continue
    except:
        pass # не нашли элемент, определяющий страницу как выбор даты рождения => проверки на возраст не было

    sleep(0.5)

    # https://brightdata.com/faqs/selenium/how-to-wait-for-page-load
    # был случай, что как-будто страница не успела загрузиться и это начальное получение имени игры упало с ошибкой, так что для надежности добавлено ожидание загрузки элемента
    try:
        title_element = EC.presence_of_element_located((By.ID, 'appHubAppName'))
        title = WebDriverWait(driver, 10).until(title_element).text
    except TimeoutException:
        print('timeout')

    try:
        game_description_snippet = driver.find_element(by=By.CLASS_NAME, value='game_description_snippet')
    except:
        log.warning(f'Не удалось получить описание для игры {game_page_url} | steam_id = {game_id}. game_description_snippet = None')
        game_description_snippet = None

    try:
        # ищем блок с ценой, где указано Купить Game Name
        # https://www.browserstack.com/guide/find-element-by-text-using-selenium
        game_price_block_title = driver.find_element(by=By.XPATH, value=f"//*[text()='Купить {title}']")
        game_price_block = game_price_block_title.find_element(by=By.XPATH, value='..')
        # если есть скидка, то там получаем ориг цену с другого элемента. В некоторых случаях просто .game_purchase_price.price для игры со скидкой может взять цену какого-то dlc (было при тесте на Subnautica). + надо будет преобразовать потом столбец, отделить валюту, в идеале парсить без впн под ру айпи чтобы все цены были в рублях
        try:
            disicont_final_price = game_price_block.find_element(by=By.CLASS_NAME, value='discount_final_price')

            # вариант ниже у меня на впн на польшу, где отдельный блок с историей цены за 30 дней и с ориг ценой в элементе normal_price (новая тема, такого никогда не было)
            try:
                game_price = game_price_block.find_element(by=By.CLASS_NAME, value='normal_price').text
            except:
                # вариант ниже если без впн (дефолт)
                try:
                    game_price = game_price_block.find_element(by=By.CLASS_NAME, value='discount_original_price').text
                except:
                    log.warning(f'Ошибка при получения цены игры со скидкой {game_page_url} | steam_id = {game_id}. game_price = None')
                    game_price = None
        except:
            try:
                game_price = game_price_block.find_element(by=By.CSS_SELECTOR, value='.game_purchase_price.price').text
            except:
                log.warning(f'Ошибка при получения цены игры без скидки {game_page_url} | steam_id = {game_id}. game_price = None')
                game_price = None
    except:
        try:
            # Если игра беслпатная, то вместо "Купить" там написано "Сыграть в"
            # https://makeseleniumeasy.com/2025/01/25/advanced-xpath-concept-method-normalize-space-its-usage/
            game_price_block_title = driver.find_element(by=By.XPATH, value=f"//h2[normalize-space(text())='Сыграть в {title}']")
            log.info(f'Бесплатная игра {game_page_url} | steam_id = {game_id}')
            game_price_block = game_price_block_title.find_element(by=By.XPATH, value='..')
            game_price = game_price_block.find_element(by=By.CSS_SELECTOR, value='.game_purchase_price.price').text
        except:
            log.warning(f'Ошибка при получения цены игры {game_page_url} | steam_id = {game_id}. game_price = None')
            game_price = None

    try:
        reviews_div = driver.find_element(by=By.CLASS_NAME, value='review_score_summaries')

        # скролл к блоку с отзывами(обзорами пользователей) - хз насколько он нужен, мб раз мы за счет селениума имитируем хождение по странице, то это типо логично
        driver.execute_script('arguments[0].scrollIntoView(true);', reviews_div) # https://sky.pro/wiki/python/prokrutka-veb-stranitsy-v-python-s-pomoschyu-selenium-web-driver/
        
        all_reviews = reviews_div.find_element(by=By.CSS_SELECTOR, value='.review_summary_ctn.overall_summary_ctn.review_box_background .summary_text')
        has_russian_reviews = False

        # Если для игры нет отзывов на русском
        if all_reviews.find_element(by=By.CLASS_NAME, value='title').text.lower() == 'все обзоры:':
            all_language_reviews_type = all_reviews.find_element(by=By.CLASS_NAME, value='game_review_summary').text
            all_language_reviews_count = int(all_reviews.find_element(by=By.CLASS_NAME, value='app_reviews_count').text.replace('(', '').replace(')', '').replace('всего', '').replace(' ', ''))

            all_russian_reviews_type = None
            all_russian_reviews_count = None
        else: # Если для игры есть отзывы на русском
            has_russian_reviews = True
            
            all_russian_reviews_type = all_reviews.find_element(by=By.CLASS_NAME, value='game_review_summary').text
            all_russian_reviews_count = int(all_reviews.find_element(by=By.CLASS_NAME, value='app_reviews_count').text.replace('(', '').replace(')', '').replace('всего', '').replace(' ', ''))

            all_language_reviews = reviews_div.find_element(by=By.CSS_SELECTOR, value='.review_language_breakdown .outlier_totals.global.review_box_background_secondary')

            all_language_reviews_count = int(all_language_reviews.find_element(by=By.CLASS_NAME, value='review_summary_count').text.replace(' ', ''))
            all_language_reviews_type = all_language_reviews.find_element(by=By.CLASS_NAME, value='game_review_summary').text
    except:
        log.warning(f'Ошибка при получения данных об обзорах/отзывов для игры {game_page_url} | steam_id = {game_id}')
        has_russian_reviews = False
        all_language_reviews_type = None
        all_language_reviews_count = None

        all_russian_reviews_type = None
        all_russian_reviews_count = None


    try:
        games_data.append({'steam_id': game_id, 'game_name': title, 'game_description_snippet': game_description_snippet.text, 'game_price': game_price, 'all_language_reviews_type': all_language_reviews_type, 'all_language_reviews_count': all_language_reviews_count, 'has_russian_reviews': has_russian_reviews, 'all_russian_reviews_type': all_russian_reviews_type, 'all_russian_reviews_count': all_russian_reviews_count, 'steam_app_url': game_page_url})
        finish = time.perf_counter()
        res = finish - start
        log.info(f'Получена игра {title} | {game_page_url} | steam_id = {game_id} | время выполнения: {res} сек')
    except:
        log.warning(f'Ошибка сохранения данных для игры {game_page_url} | steam_id = {game_id}')

driver.quit()

df = pd.DataFrame(games_data)
log.info(f'Датасет собран, {df.shape[0]} строк')
df_filename = f'games_data_[{int(selected_slice[0])}-{int(selected_slice[1])}].xlsx'
df.to_excel(root_path / 'data' / df_filename, index=False)
total_finish = time.perf_counter()
total_res = total_finish - total_start
log.info(f'Датасет сохранен в файл {df_filename} | время выполнения: {total_res} сек')