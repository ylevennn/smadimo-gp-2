import requests
import time
import pandas as pd

# ============================================================
# 1. Получаем инди-игры из SteamSpy (одна страница = все данные)
# ============================================================

url = 'https://steamspy.com/api.php?request=tag&tag=Indie'
r = requests.get(url)
data = r.json()

indie_list = []
for appid, info in data.items():
    info['appid'] = int(appid)
    indie_list.append(info)

df_spy = pd.DataFrame(indie_list)
df_spy = df_spy.drop_duplicates(subset='appid')

print(f'Инди-игр из SteamSpy: {len(df_spy)}')
print(f'Столбцы: {df_spy.columns.tolist()}')
print(df_spy.head())

# ============================================================
# 2. Мёржим с IStoreService данными
# ============================================================

df_store = pd.read_csv('steam_all_games.csv')
df_merged = df_spy.merge(df_store[['appid', 'last_modified', 'price_change_number']],
                         on='appid', how='left')

print(f'\nПосле мёржа: {len(df_merged)}')
print(df_merged.head())

# ============================================================
# 3. Считаем positive_ratio и total_reviews
# ============================================================

df_merged['total_reviews'] = df_merged['positive'] + df_merged['negative']
df_merged['positive_ratio'] = (df_merged['positive'] / df_merged['total_reviews']).round(4)

# убираем игры без обзоров
df_merged = df_merged[df_merged['total_reviews'] > 0]
print(f'С обзорами: {len(df_merged)}')

# ============================================================
# 4. Сохраняем базовый датасет инди-игр
# ============================================================

df_merged.to_csv('indie_games_base.csv', index=False)
print(f'\nСохранено в indie_games_base.csv')
print(f'Размер: {df_merged.shape}')
print(f'\nСтатистика:')
print(df_merged[['positive', 'negative', 'total_reviews', 'positive_ratio', 'price', 'ccu']].describe())
