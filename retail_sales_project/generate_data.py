"""Генерация датасета розничных продаж → data/sales_data.csv"""
import pandas as pd, numpy as np, os
from datetime import datetime, timedelta

np.random.seed(42)

regions = {'S01':'Москва','S02':'Москва','S03':'Москва',
           'S04':'Санкт-Петербург','S05':'Санкт-Петербург',
           'S06':'Казань','S07':'Екатеринбург',
           'S08':'Новосибирск','S09':'Ростов-на-Дону','S10':'Самара'}

catalog = {
    'Электроника':     [('Смартфон',25000),('Наушники',3500),('Планшет',18000),('Колонка',5500)],
    'Одежда':          [('Куртка',8500),('Джинсы',4200),('Футболка',1800),('Кроссовки',6500)],
    'Продукты':        [('Кофе 1кг',900),('Чай 100п',450),('Шоколад',250),('Мёд 500г',600)],
    'Бытовая техника': [('Чайник',3200),('Пылесос',12000),('Утюг',4500),('Блендер',5000)],
    'Канцтовары':      [('Набор ручек',350),('Ежедневник',700),('Калькулятор',1200),('Степлер',450)],
}
margins = {'Электроника':.22,'Одежда':.45,'Продукты':.30,'Бытовая техника':.28,'Канцтовары':.50}

rows = []
start, n_days = datetime(2023,1,1), (datetime(2025,12,31)-datetime(2023,1,1)).days
for _ in range(2500):
    dt = start + timedelta(days=int(np.random.randint(0, n_days)))
    m = dt.month
    season = {12:1.6, 11:1.2, 1:1.2}.get(m, 0.85 if m in (6,7,8) else 1.0)
    store = np.random.choice(list(regions))
    cat = np.random.choice(list(catalog))
    prod, bp = catalog[cat][np.random.randint(len(catalog[cat]))]
    price = round(bp * np.random.uniform(.9,1.15), 2)
    qty = max(1, int(np.random.exponential(3)*season))
    rev = round(price*qty, 2)
    cost = round(rev*(1 - margins[cat]*np.random.uniform(.8,1.2)), 2)
    rows.append(dict(date=dt.strftime('%Y-%m-%d'), store_id=store, region=regions[store],
                     category=cat, product=prod, quantity=qty, unit_price=price, revenue=rev, cost=cost))

df = pd.DataFrame(rows)
for c in ['quantity','unit_price','revenue']:
    df.loc[np.random.rand(len(df))<.03, c] = np.nan
df = df.sample(frac=1, random_state=0).reset_index(drop=True)

os.makedirs('data', exist_ok=True)
df.to_csv('data/sales_data.csv', index=False, encoding='utf-8-sig')
print(f'Создано {len(df)} строк → data/sales_data.csv')
