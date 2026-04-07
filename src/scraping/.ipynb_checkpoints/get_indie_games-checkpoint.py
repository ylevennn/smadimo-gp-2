import requests
import pandas as pd
# https://sky.pro/wiki/python/poluchenie-puti-k-kornevoy-strukture-proekta-v-python/
from pathlib import Path
# https://www.geeksforgeeks.org/python/python-import-from-parent-directory/
import sys

root_path = Path(__file__).resolve().parents[2] # поднимается вверх на 2 директории
sys.path.append(str(root_path))
from src.logs.logger import logger

log = logger()

data = requests.get('https://steamspy.com/api.php?request=tag&tag=Indie').json()
log.info(f'Получены {len(data)} строк с Инди играми со SteamSpy')

indie_games = []

for app_id in data:
  app_i = data[app_id]
  try:
    indie_games.append({'steam_app_id': app_id, 'name': app_i['name']})
  except Exception as e:
    log.error(f'Ошибка при добавлении игры {app_id} в массив. {e}')

df = pd.DataFrame(indie_games)
log.info(f'Датасет собран, {df.shape[0]} строк')
df.to_excel(root_path / 'data' / 'indie_games.xlsx', index=False)
log.info(f'Датасет сохранен в файл indie_games.xlsx')