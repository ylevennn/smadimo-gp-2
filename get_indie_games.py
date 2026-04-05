import requests
import pandas as pd

data = requests.get('https://steamspy.com/api.php?request=tag&tag=Indie').json()

indie_games = []

for app_id in data:
  app_i = data[app_id]
  indie_games.append({'steam_app_id': app_id, 'name': app_i['name']})

df = pd.DataFrame(indie_games)
df.to_excel('indie_games.xlsx', index=False)