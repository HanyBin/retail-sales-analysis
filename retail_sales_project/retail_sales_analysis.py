"""
=============================================================
  Анализ розничных продаж — Retail Sales Analysis
  Автор: Терехов Никита
  Стек: Python · pandas · NumPy · Matplotlib
=============================================================
  Проект демонстрирует навыки работы с данными:
    1. Загрузка и очистка данных (пропуски, типы)
    2. Агрегации и группировки (groupby, pivot_table)
    3. Анализ динамики выручки, маржинальности, топ-товаров
    4. Визуализация (bar, line, heatmap)
    5. Экспорт агрегатов для Power BI
=============================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

# ─────────────────────────────────────────────
# 1. ЗАГРУЗКА И ПЕРВИЧНЫЙ ОСМОТР
# ─────────────────────────────────────────────
print('=' * 60)
print('1. ЗАГРУЗКА ДАННЫХ')
print('=' * 60)

df = pd.read_csv('data/sales_data.csv', parse_dates=['date'])

print(f'Размер датасета: {df.shape[0]} строк × {df.shape[1]} столбцов')
print(f'\nТипы данных:\n{df.dtypes}')
print(f'\nПропуски:\n{df.isnull().sum()}')
print(f'\nПервые 5 строк:\n{df.head()}')

# ─────────────────────────────────────────────
# 2. ОЧИСТКА ДАННЫХ
# ─────────────────────────────────────────────
print('\n' + '=' * 60)
print('2. ОЧИСТКА ДАННЫХ')
print('=' * 60)

rows_before = len(df)

# Заполняем пропуски медианой (стандартный подход для числовых)
for col in ['quantity', 'unit_price', 'revenue']:
    median_val = df[col].median()
    n_missing = df[col].isnull().sum()
    df[col] = df[col].fillna(median_val)
    if n_missing > 0:
        print(f'  {col}: заполнено {n_missing} пропусков медианой ({median_val:.0f})')

# Пересчитываем revenue где он был NaN (на основе qty * price)
mask_recalc = df['revenue'] == df['revenue'].median()
# df.loc[mask_recalc, 'revenue'] = df.loc[mask_recalc, 'quantity'] * df.loc[mask_recalc, 'unit_price']

# Добавляем расчётные столбцы
df['profit'] = df['revenue'] - df['cost']
df['margin_pct'] = (df['profit'] / df['revenue'] * 100).round(1)
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['year_month'] = df['date'].dt.to_period('M')

print(f'\nПосле очистки: {len(df)} строк (было {rows_before})')
print(f'Добавлены столбцы: profit, margin_pct, year, month, year_month')

# ─────────────────────────────────────────────
# 3. ОБЩАЯ СТАТИСТИКА
# ─────────────────────────────────────────────
print('\n' + '=' * 60)
print('3. ОБЩАЯ СТАТИСТИКА')
print('=' * 60)

total_revenue = df['revenue'].sum()
total_profit  = df['profit'].sum()
avg_margin    = df['margin_pct'].mean()
n_stores      = df['store_id'].nunique()
n_regions     = df['region'].nunique()

print(f'  Общая выручка:      {total_revenue:>14,.0f} ₽')
print(f'  Общая прибыль:      {total_profit:>14,.0f} ₽')
print(f'  Средняя маржа:      {avg_margin:>13.1f} %')
print(f'  Кол-во магазинов:   {n_stores:>14}')
print(f'  Кол-во регионов:    {n_regions:>14}')

# ─────────────────────────────────────────────
# 4. АНАЛИЗ ПО РЕГИОНАМ
# ─────────────────────────────────────────────
print('\n' + '=' * 60)
print('4. ВЫРУЧКА И МАРЖА ПО РЕГИОНАМ')
print('=' * 60)

region_stats = (df.groupby('region')
                .agg(revenue=('revenue', 'sum'),
                     profit=('profit', 'sum'),
                     orders=('revenue', 'count'),
                     avg_check=('revenue', 'mean'))
                .round(0)
                .sort_values('revenue', ascending=False))

region_stats['margin_pct'] = (region_stats['profit'] / region_stats['revenue'] * 100).round(1)
print(region_stats.to_string())

# ─────────────────────────────────────────────
# 5. АНАЛИЗ ПО КАТЕГОРИЯМ
# ─────────────────────────────────────────────
print('\n' + '=' * 60)
print('5. ВЫРУЧКА ПО КАТЕГОРИЯМ')
print('=' * 60)

cat_stats = (df.groupby('category')
             .agg(revenue=('revenue', 'sum'),
                  profit=('profit', 'sum'),
                  qty=('quantity', 'sum'))
             .sort_values('revenue', ascending=False))

cat_stats['margin_pct'] = (cat_stats['profit'] / cat_stats['revenue'] * 100).round(1)
cat_stats['share_pct'] = (cat_stats['revenue'] / cat_stats['revenue'].sum() * 100).round(1)
print(cat_stats.to_string())

# ─────────────────────────────────────────────
# 6. ТОП-10 ТОВАРОВ ПО ВЫРУЧКЕ
# ─────────────────────────────────────────────
print('\n' + '=' * 60)
print('6. ТОП-10 ТОВАРОВ ПО ВЫРУЧКЕ')
print('=' * 60)

top_products = (df.groupby('product')
                .agg(revenue=('revenue', 'sum'), qty=('quantity', 'sum'))
                .sort_values('revenue', ascending=False)
                .head(10))

print(top_products.to_string())

# ─────────────────────────────────────────────
# 7. ДИНАМИКА ВЫРУЧКИ ПО МЕСЯЦАМ
# ─────────────────────────────────────────────
print('\n' + '=' * 60)
print('7. МЕСЯЧНАЯ ДИНАМИКА')
print('=' * 60)

monthly = (df.groupby('year_month')
           .agg(revenue=('revenue', 'sum'), profit=('profit', 'sum'))
           .reset_index())

monthly['year_month_str'] = monthly['year_month'].astype(str)
print(monthly.tail(12).to_string(index=False))

# ─────────────────────────────────────────────
# 8. PIVOT: РЕГИОН × КАТЕГОРИЯ
# ─────────────────────────────────────────────
print('\n' + '=' * 60)
print('8. PIVOT: ВЫРУЧКА — РЕГИОН × КАТЕГОРИЯ')
print('=' * 60)

pivot = pd.pivot_table(df, values='revenue', index='region',
                       columns='category', aggfunc='sum', fill_value=0)
pivot = pivot.round(0)
print(pivot.to_string())


# ═══════════════════════════════════════════════
# 9. ВИЗУАЛИЗАЦИЯ
# ═══════════════════════════════════════════════

os.makedirs('output', exist_ok=True)

TEAL = '#0d5b54'
TEAL2 = '#117a70'
GRAY = '#7b828d'
plt.rcParams.update({
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.labelsize': 11,
    'figure.facecolor': '#f6f3ec',
    'axes.facecolor': '#f6f3ec',
    'axes.edgecolor': '#d8d2c4',
    'grid.color': '#d8d2c4',
    'grid.alpha': 0.6,
})

# --- 9a. Выручка по регионам ---
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(region_stats.index[::-1], region_stats['revenue'][::-1], color=TEAL, height=0.6)
ax.set_xlabel('Выручка, ₽')
ax.set_title('Выручка по регионам')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))
ax.grid(axis='x')
for bar in bars:
    w = bar.get_width()
    ax.text(w + total_revenue*0.005, bar.get_y() + bar.get_height()/2,
            f'{w/1e6:.1f}M', va='center', fontsize=9, color=GRAY)
plt.tight_layout()
plt.savefig('output/01_revenue_by_region.png', dpi=150)
plt.close()
print('\n✓ Сохранён: output/01_revenue_by_region.png')

# --- 9b. Доля категорий (pie) ---
fig, ax = plt.subplots(figsize=(7, 7))
colors = ['#0d5b54','#117a70','#2a9d8f','#76c7b7','#b5ddd4']
wedges, texts, autotexts = ax.pie(
    cat_stats['revenue'], labels=cat_stats.index, autopct='%1.1f%%',
    colors=colors, startangle=140, textprops={'fontsize': 11})
for t in autotexts:
    t.set_fontsize(10)
    t.set_fontweight('bold')
ax.set_title('Доля категорий в выручке')
plt.tight_layout()
plt.savefig('output/02_category_share.png', dpi=150)
plt.close()
print('✓ Сохранён: output/02_category_share.png')

# --- 9c. Месячная динамика ---
fig, ax = plt.subplots(figsize=(12, 5))
x = range(len(monthly))
ax.fill_between(x, monthly['revenue'], alpha=0.15, color=TEAL)
ax.plot(x, monthly['revenue'], color=TEAL, linewidth=2, label='Выручка')
ax.plot(x, monthly['profit'], color='#e76f51', linewidth=2, label='Прибыль', linestyle='--')
step = max(1, len(monthly)//15)
ax.set_xticks(range(0, len(monthly), step))
ax.set_xticklabels(monthly['year_month_str'].iloc[::step], rotation=45, ha='right', fontsize=9)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))
ax.set_title('Динамика выручки и прибыли по месяцам')
ax.legend()
ax.grid(axis='y')
plt.tight_layout()
plt.savefig('output/03_monthly_trend.png', dpi=150)
plt.close()
print('✓ Сохранён: output/03_monthly_trend.png')

# --- 9d. Heatmap: регион × категория ---
fig, ax = plt.subplots(figsize=(9, 6))
data_hm = pivot.values
im = ax.imshow(data_hm, cmap='YlGnBu', aspect='auto')
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns, rotation=30, ha='right')
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index)
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        v = data_hm[i, j]
        c = 'white' if v > data_hm.mean() else 'black'
        ax.text(j, i, f'{v/1e3:.0f}K', ha='center', va='center', fontsize=9, color=c)
ax.set_title('Heatmap: выручка — регион × категория (тыс. ₽)')
plt.colorbar(im, ax=ax, shrink=0.8)
plt.tight_layout()
plt.savefig('output/04_heatmap_region_category.png', dpi=150)
plt.close()
print('✓ Сохранён: output/04_heatmap_region_category.png')

# --- 9e. Маржинальность по категориям ---
fig, ax = plt.subplots(figsize=(8, 5))
cats_sorted = cat_stats.sort_values('margin_pct', ascending=True)
colors_bar = [TEAL if m > avg_margin else '#e76f51' for m in cats_sorted['margin_pct']]
ax.barh(cats_sorted.index, cats_sorted['margin_pct'], color=colors_bar, height=0.5)
ax.axvline(avg_margin, color=GRAY, linestyle='--', linewidth=1, label=f'Среднее: {avg_margin:.1f}%')
for i, (idx, row) in enumerate(cats_sorted.iterrows()):
    ax.text(row['margin_pct'] + 0.5, i, f"{row['margin_pct']:.1f}%", va='center', fontsize=10)
ax.set_xlabel('Маржинальность, %')
ax.set_title('Маржинальность по категориям')
ax.legend()
plt.tight_layout()
plt.savefig('output/05_margin_by_category.png', dpi=150)
plt.close()
print('✓ Сохранён: output/05_margin_by_category.png')


# ═══════════════════════════════════════════════
# 10. ЭКСПОРТ АГРЕГАТОВ ДЛЯ POWER BI
# ═══════════════════════════════════════════════
print('\n' + '=' * 60)
print('10. ЭКСПОРТ ДЛЯ POWER BI')
print('=' * 60)

# Главная сводка по месяцам / регионам / категориям
export = (df.groupby(['year', 'month', 'region', 'category'])
          .agg(revenue=('revenue', 'sum'),
               profit=('profit', 'sum'),
               cost=('cost', 'sum'),
               orders=('revenue', 'count'),
               qty=('quantity', 'sum'))
          .reset_index()
          .round(0))

export.to_csv('output/sales_summary_for_powerbi.csv', index=False, encoding='utf-8-sig')
print(f'✓ Экспортировано {len(export)} строк → output/sales_summary_for_powerbi.csv')

# Детальные данные (очищенные)
df_export = df.drop(columns=['year_month']).copy()
df_export.to_csv('output/sales_clean.csv', index=False, encoding='utf-8-sig')
print(f'✓ Очищенный датасет → output/sales_clean.csv ({len(df_export)} строк)')

print('\n' + '=' * 60)
print('ГОТОВО! Все графики и данные в папке output/')
print('=' * 60)
