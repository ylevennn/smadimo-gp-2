import time

import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def get_steamcharts(appid):
    url = f"https://steamcharts.com/app/{appid}"
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    result = {"appid": appid}

    # current, 24h peak, all-time peak — три блока в шапке
    stats = soup.select("div.app-stat span.num")
    if len(stats) >= 3:
        result["current_players"] = int(stats[0].text.strip().replace(",", ""))
        result["peak_24h"] = int(stats[1].text.strip().replace(",", ""))
        result["peak_all_time"] = int(stats[2].text.strip().replace(",", ""))

    # последний месяц из таблицы — avg players
    rows = soup.select("table.common-table tbody tr")
    if rows:
        cells = rows[0].select("td")
        if len(cells) >= 5:
            avg_text = cells[1].text.strip().replace(",", "")
            gain_text = cells[2].text.strip().replace(",", "")
            gain_pct_text = cells[3].text.strip()
            peak_text = cells[4].text.strip().replace(",", "")

            try:
                result["avg_players_last_month"] = float(avg_text)
            except:
                result["avg_players_last_month"] = None
            try:
                result["peak_last_month"] = int(float(peak_text))
            except:
                result["peak_last_month"] = None

    return result


# ============================================================
# Тест на нескольких играх
# ============================================================

test_ids = [
    (105600, "Terraria"),
    (578080, "PUBG"),
    (1145360, "Hades"),
    (413150, "Stardew Valley"),
    (367520, "Hollow Knight"),
]

for appid, name in test_ids:
    data = get_steamcharts(appid)
    print(f"{name}: {data}")
    time.sleep(0.5)
