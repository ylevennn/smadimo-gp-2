import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument(
    "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.navigator.chrome = {runtime: {}};
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    """
    },
)

driver.get("https://howlongtobeat.com/game/102201")
time.sleep(5)

# закрываем cookie-баннер если есть
try:
    cookie_btn = driver.find_element(
        By.CSS_SELECTOR,
        'button[aria-label="Consent"], button.fc-cta-consent, button[title="Consent"]',
    )
    cookie_btn.click()
    time.sleep(1)
except:
    pass

# ============================================================
# Вспомогательные функции
# ============================================================


def parse_time(text):
    text = text.strip().replace("½", ".5")
    if text == "--" or text == "":
        return None
    hours = 0
    h_match = re.search(r"(\d+\.?\d*)\s*[hH]", text)
    m_match = re.search(r"(\d+\.?\d*)\s*m", text)
    if h_match:
        hours += float(h_match.group(1))
    if m_match:
        hours += float(m_match.group(1)) / 60
    if not h_match and not m_match:
        num = re.search(r"(\d+\.?\d*)", text)
        if num:
            hours = float(num.group(1))
    return round(hours, 2) if hours > 0 else None


def parse_count(match):
    if not match:
        return None
    val = match.group(1)
    if "K" in val:
        return int(float(val.replace("K", "")) * 1000)
    return int(val)


# ============================================================
# Название — берём из title страницы
# "How long is Palworld? | HowLongToBeat" -> "Palworld"
# ============================================================

page_title = driver.title
title_match = re.search(r"How long is (.+?)\?", page_title)
title = title_match.group(1).strip() if title_match else page_title

page_text = driver.find_element(By.TAG_NAME, "body").text

# рейтинг и retirement
rating_match = re.search(r"(\d+)%\s*Rating", page_text)
retirement_match = re.search(r"(\d+\.?\d*)%\s*Retired", page_text) or re.search(
    r"(\d+\.?\d*)%\s*Retirement", page_text
)
rating = int(rating_match.group(1)) if rating_match else None
retirement = float(retirement_match.group(1)) if retirement_match else None

# playing, backlogs, beat
playing = parse_count(re.search(r"(\d+(?:\.\d+)?K?)\s*Playing", page_text))
backlogs = parse_count(re.search(r"(\d+(?:\.\d+)?K?)\s*Backlogs?", page_text))
beat = parse_count(re.search(r"(\d+(?:\.\d+)?K?)\s*Beat", page_text))

# описание
desc_match = re.search(r"Palworld is (.+?)How long is", page_text, re.DOTALL)
description = (
    desc_match.group(0).replace("How long is", "").strip() if desc_match else ""
)
# более универсально — берём текст между заголовками
desc_match2 = re.search(
    rf"{re.escape(title)} is (.+?)How long is", page_text, re.DOTALL
)
description = desc_match2.group(1).strip() if desc_match2 else ""

# жанры и разработчик
genres_match = re.search(r"Genres?:\s*(.+?)(?:Developer|$)", page_text)
developer_match = re.search(r"Developer:\s*(.+?)(?:Publisher|$)", page_text)
publisher_match = re.search(r"Publisher:\s*(.+?)(?:NA:|EU:|JP:|Updated|$)", page_text)

genres = genres_match.group(1).strip() if genres_match else ""
developer = developer_match.group(1).strip() if developer_match else ""
publisher = publisher_match.group(1).strip() if publisher_match else ""

game_data = {
    "title": title,
    "description": description,
    "genres": genres,
    "developer": developer,
    "publisher": publisher,
    "rating": rating,
    "retirement": retirement,
    "playing": playing,
    "backlogs": backlogs,
    "beat": beat,
}

# ============================================================
# Таблицы
# ============================================================

tables = driver.find_elements(By.TAG_NAME, "table")

# Таблица 0: Single-Player
if len(tables) > 0:
    rows = tables[0].find_elements(By.CSS_SELECTOR, "tbody tr")
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) >= 4:
            label = cells[0].text.strip()
            polled = cells[1].text.strip()
            average = cells[2].text.strip()
            median = cells[3].text.strip()

            if "Main Story" in label:
                game_data["sp_main_polled"] = int(polled) if polled.isdigit() else None
                game_data["sp_main_avg"] = parse_time(average)
                game_data["sp_main_median"] = parse_time(median)
            elif "Main + Extra" in label:
                game_data["sp_extras_polled"] = (
                    int(polled) if polled.isdigit() else None
                )
                game_data["sp_extras_avg"] = parse_time(average)
                game_data["sp_extras_median"] = parse_time(median)
            elif "Completionist" in label:
                game_data["sp_complete_polled"] = (
                    int(polled) if polled.isdigit() else None
                )
                game_data["sp_complete_avg"] = parse_time(average)
                game_data["sp_complete_median"] = parse_time(median)
            elif "All PlayStyles" in label:
                game_data["sp_all_polled"] = int(polled) if polled.isdigit() else None
                game_data["sp_all_avg"] = parse_time(average)
                game_data["sp_all_median"] = parse_time(median)

# Таблица 1: Multi-Player
if len(tables) > 1:
    header = tables[1].text.split("\n")[0]
    if "Multi" in header:
        rows = tables[1].find_elements(By.CSS_SELECTOR, "tbody tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:
                label = cells[0].text.strip()
                polled = cells[1].text.strip()
                average = cells[2].text.strip()
                if "Co-Op" in label:
                    game_data["mp_coop_polled"] = (
                        int(polled) if polled.isdigit() else None
                    )
                    game_data["mp_coop_avg"] = parse_time(average)
                elif "Competitive" in label:
                    game_data["mp_comp_polled"] = (
                        int(polled) if polled.isdigit() else None
                    )
                    game_data["mp_comp_avg"] = parse_time(average)

# Таблица Platform (последняя таблица с "Platform" в заголовке)
for table in tables:
    header = table.text.split("\n")[0]
    if "Platform" in header:
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        platforms = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 4:
                platforms.append(
                    {
                        "platform": cells[0].text.strip(),
                        "polled": int(cells[1].text.strip())
                        if cells[1].text.strip().isdigit()
                        else None,
                        "main_time": parse_time(cells[2].text.strip()),
                    }
                )

        game_data["platforms_list"] = ", ".join([p["platform"] for p in platforms])
        game_data["platforms_count"] = len(platforms)

        total_polled = sum(p["polled"] for p in platforms if p["polled"])
        pc = next((p for p in platforms if p["platform"] == "PC"), None)
        game_data["pc_polled_ratio"] = (
            round(pc["polled"] / total_polled, 4)
            if pc and pc["polled"] and total_polled
            else None
        )

driver.quit()

# ============================================================
# Результат
# ============================================================

print("=" * 60)
print("СОБРАННЫЕ ДАННЫЕ:")
print("=" * 60)
for k, v in game_data.items():
    print(f"  {k}: {v}")
