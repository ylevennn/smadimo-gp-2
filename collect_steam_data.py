from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
import pandas as pd

indie_games = pd.read_excel('indie_games.xlsx')
games_ids = indie_games['steam_app_id'].to_list()
games_data = []

game_page_base_url = 'https://store.steampowered.com/app/'
driver = webdriver.Chrome()

# пока работает на тестовой выборке из первых 10 + рандом игра без русских отзывов + игра со скидкой
for game_id in [1065850, 848450] + games_ids[0:10]:
    game_page_url = game_page_base_url + str(game_id) + '/'

    driver.get(game_page_url)

    # Страница с проверкой на возраст: выбрать нужный возраст и открыть страницу с игрой
    try:
        select_birthday_date = driver.find_element(by=By.CLASS_NAME, value='agegate_birthday_desc')

        select_year = Select(driver.find_element(by=By.NAME, value='ageYear'))
        select_year.select_by_value('2000')

        open_game_page_button = driver.find_element(by=By.ID, value='view_product_page_btn')
        open_game_page_button.click()
    except:
        pass

    title = driver.find_element(by=By.ID, value='appHubAppName').text

    sleep(0.5)

    game_description_snippet = driver.find_element(by=By.CLASS_NAME, value='game_description_snippet')

    # если есть скидка, то там получаем ориг цену с другого элемента. В некоторых случаях просто .game_purchase_price.price для игры со скидкой может взять цену какого-то dlc (было при тесте на Subnautica). + надо будет преобразовать потом столбец, отделить валюту, в идеале парсить без впн под ру айпи чтобы все цены были в рублях
    try:
        disicont_final_price = driver.find_element(by=By.CLASS_NAME, value='discount_final_price')

        # вариант ниже (закомментированный) меня на впн на польшу, где отдельный блок с историей цены за 30 дней и с ориг ценой в элементе normal_price (новая тема, такого никогда не было)
        ### game_price = driver.find_element(by=By.CLASS_NAME, value='normal_price') 

        # вариант ниже если без впн (дефолт)
        game_price = driver.find_element(by=By.CLASS_NAME, value='discount_original_price') 
    except:
        game_price = driver.find_element(by=By.CSS_SELECTOR, value='.game_purchase_price.price')

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


    games_data.append({'steam_id': game_id, 'game_name': title, 'game_description_snippet': game_description_snippet.text, 'game_price': game_price.text, 'all_language_reviews_type': all_language_reviews_type, 'all_language_reviews_count': all_language_reviews_count, 'has_russian_reviews': has_russian_reviews, 'all_russian_reviews_type': all_russian_reviews_type, 'all_russian_reviews_count': all_russian_reviews_count, 'steam_app_url': game_page_url})

driver.quit()

df = pd.DataFrame(games_data)
df.to_excel('games_data_test.xlsx', index=False)