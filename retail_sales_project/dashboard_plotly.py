"""
=============================================================
  Интерактивный дашборд — Plotly
  Автор: Терехов Никита
  Генерирует output/dashboard.html (открывается в любом браузере)
=============================================================
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import os

# ─── Загрузка данных ───
df = pd.read_csv('data/sales_data.csv', parse_dates=['date'])
for col in ['quantity', 'unit_price', 'revenue']:
    df[col] = df[col].fillna(df[col].median())
df['profit'] = df['revenue'] - df['cost']
df['margin_pct'] = (df['profit'] / df['revenue'] * 100).round(1)
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['year_month'] = df['date'].dt.to_period('M').astype(str)

# ─── Цветовая схема ───
TEAL = '#0d5b54'
TEAL2 = '#117a70'
CORAL = '#e76f51'
BG = '#f6f3ec'
CARD_BG = '#ffffff'
GRAY = '#7b828d'
PALETTE = ['#0d5b54', '#2a9d8f', '#76c7b7', '#e76f51', '#f4a261']

# ─── KPI ───
total_rev = df['revenue'].sum()
total_profit = df['profit'].sum()
total_orders = len(df)
avg_margin = df['margin_pct'].mean()

# ─── Агрегаты ───
monthly = df.groupby('year_month').agg(
    revenue=('revenue', 'sum'), profit=('profit', 'sum')
).reset_index()

by_region = df.groupby('region').agg(
    revenue=('revenue', 'sum')
).sort_values('revenue', ascending=True).reset_index()

by_cat = df.groupby('category').agg(
    revenue=('revenue', 'sum'), profit=('profit', 'sum')
).reset_index()
by_cat['margin'] = (by_cat['profit'] / by_cat['revenue'] * 100).round(1)
by_cat = by_cat.sort_values('revenue', ascending=False)

pivot = pd.pivot_table(df, values='revenue', index='region',
                       columns='category', aggfunc='sum', fill_value=0)

top10 = df.groupby('product').agg(
    revenue=('revenue', 'sum'), qty=('quantity', 'sum')
).sort_values('revenue', ascending=False).head(10).reset_index()

# ─── Построение дашборда ───

# Создаём HTML вручную с несколькими графиками
figures_html = []

# 1. Месячная динамика
fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=monthly['year_month'], y=monthly['revenue'],
    mode='lines', name='Выручка', line=dict(color=TEAL, width=2.5),
    fill='tozeroy', fillcolor='rgba(13,91,84,0.08)'
))
fig1.add_trace(go.Scatter(
    x=monthly['year_month'], y=monthly['profit'],
    mode='lines', name='Прибыль', line=dict(color=CORAL, width=2, dash='dash')
))
fig1.update_layout(
    title='Динамика выручки и прибыли по месяцам',
    xaxis_title='', yaxis_title='₽',
    hovermode='x unified', template='plotly_white',
    plot_bgcolor=BG, paper_bgcolor=BG,
    font=dict(family='system-ui, sans-serif'),
    height=380, margin=dict(t=50, b=40, l=60, r=20),
    legend=dict(orientation='h', y=1.12)
)
figures_html.append(fig1.to_html(full_html=False, include_plotlyjs=False))

# 2. Выручка по регионам
fig2 = go.Figure(go.Bar(
    x=by_region['revenue'], y=by_region['region'],
    orientation='h', marker_color=TEAL,
    text=[f'{v/1e6:.1f}M' for v in by_region['revenue']],
    textposition='outside'
))
fig2.update_layout(
    title='Выручка по регионам',
    xaxis_title='₽', yaxis_title='',
    template='plotly_white', plot_bgcolor=BG, paper_bgcolor=BG,
    font=dict(family='system-ui, sans-serif'),
    height=350, margin=dict(t=50, b=40, l=130, r=60)
)
figures_html.append(fig2.to_html(full_html=False, include_plotlyjs=False))

# 3. Доля категорий
fig3 = go.Figure(go.Pie(
    labels=by_cat['category'], values=by_cat['revenue'],
    hole=0.45, marker=dict(colors=PALETTE),
    textinfo='label+percent', textposition='outside'
))
fig3.update_layout(
    title='Доля категорий в выручке',
    template='plotly_white', plot_bgcolor=BG, paper_bgcolor=BG,
    font=dict(family='system-ui, sans-serif'),
    height=380, margin=dict(t=50, b=20, l=20, r=20),
    showlegend=False
)
figures_html.append(fig3.to_html(full_html=False, include_plotlyjs=False))

# 4. Маржинальность по категориям
by_cat_sorted = by_cat.sort_values('margin', ascending=True)
fig4 = go.Figure(go.Bar(
    x=by_cat_sorted['margin'], y=by_cat_sorted['category'],
    orientation='h',
    marker_color=[TEAL if m > avg_margin else CORAL for m in by_cat_sorted['margin']],
    text=[f'{m:.1f}%' for m in by_cat_sorted['margin']],
    textposition='outside'
))
fig4.add_vline(x=avg_margin, line_dash='dash', line_color=GRAY,
               annotation_text=f'Среднее: {avg_margin:.1f}%')
fig4.update_layout(
    title='Маржинальность по категориям',
    xaxis_title='%', yaxis_title='',
    template='plotly_white', plot_bgcolor=BG, paper_bgcolor=BG,
    font=dict(family='system-ui, sans-serif'),
    height=320, margin=dict(t=50, b=40, l=130, r=60)
)
figures_html.append(fig4.to_html(full_html=False, include_plotlyjs=False))

# 5. Heatmap: регион × категория
fig5 = go.Figure(go.Heatmap(
    z=pivot.values,
    x=pivot.columns.tolist(),
    y=pivot.index.tolist(),
    colorscale='Teal',
    text=[[f'{v/1e3:.0f}K' for v in row] for row in pivot.values],
    texttemplate='%{text}',
    hovertemplate='%{y} · %{x}<br>Выручка: %{z:,.0f} ₽<extra></extra>'
))
fig5.update_layout(
    title='Heatmap: выручка — регион × категория',
    template='plotly_white', plot_bgcolor=BG, paper_bgcolor=BG,
    font=dict(family='system-ui, sans-serif'),
    height=380, margin=dict(t=50, b=80, l=130, r=20)
)
figures_html.append(fig5.to_html(full_html=False, include_plotlyjs=False))

# 6. Топ-10 товаров
fig6 = go.Figure(go.Bar(
    x=top10['revenue'], y=top10['product'],
    orientation='h', marker_color=TEAL2,
    text=[f'{v/1e6:.2f}M' for v in top10['revenue']],
    textposition='outside'
))
fig6.update_layout(
    title='Топ-10 товаров по выручке',
    xaxis_title='₽', yaxis_title='',
    template='plotly_white', plot_bgcolor=BG, paper_bgcolor=BG,
    font=dict(family='system-ui, sans-serif'),
    height=380, margin=dict(t=50, b=40, l=110, r=60),
    yaxis=dict(autorange='reversed')
)
figures_html.append(fig6.to_html(full_html=False, include_plotlyjs=False))


# ─── Сборка HTML-страницы ───
html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Дашборд — Анализ розничных продаж</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{font-family:system-ui,-apple-system,sans-serif;background:{BG};color:#15171c;}}
  .header{{background:{TEAL};color:#fff;padding:28px 32px 22px;}}
  .header h1{{font-size:26px;font-weight:700;letter-spacing:-.3px;}}
  .header p{{font-size:13px;opacity:.8;margin-top:4px;}}
  .kpi-row{{display:flex;gap:16px;padding:20px 32px;flex-wrap:wrap;}}
  .kpi{{background:{CARD_BG};border-radius:10px;padding:18px 22px;flex:1;min-width:160px;
    box-shadow:0 1px 6px rgba(0,0,0,.06);border:1px solid #e8e4db;}}
  .kpi .label{{font-size:11px;text-transform:uppercase;letter-spacing:1.2px;color:{GRAY};font-weight:700;}}
  .kpi .value{{font-size:26px;font-weight:800;color:{TEAL};margin-top:4px;}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;padding:8px 32px 32px;}}
  .card{{background:{CARD_BG};border-radius:10px;padding:16px;
    box-shadow:0 1px 6px rgba(0,0,0,.06);border:1px solid #e8e4db;}}
  .card.wide{{grid-column:1/-1;}}
  .footer{{text-align:center;padding:16px;font-size:12px;color:{GRAY};}}
  @media(max-width:800px){{.grid{{grid-template-columns:1fr;}}.kpi-row{{flex-direction:column;}}}}
</style>
</head>
<body>
  <div class="header">
    <h1>Анализ розничных продаж</h1>
    <p>Python · pandas · Plotly · 2023–2025 · Терехов Никита</p>
  </div>

  <div class="kpi-row">
    <div class="kpi"><div class="label">Выручка</div><div class="value">{total_rev/1e6:.1f}M ₽</div></div>
    <div class="kpi"><div class="label">Прибыль</div><div class="value">{total_profit/1e6:.1f}M ₽</div></div>
    <div class="kpi"><div class="label">Заказов</div><div class="value">{total_orders:,}</div></div>
    <div class="kpi"><div class="label">Средняя маржа</div><div class="value">{avg_margin:.1f}%</div></div>
  </div>

  <div class="grid">
    <div class="card wide">{figures_html[0]}</div>
    <div class="card">{figures_html[1]}</div>
    <div class="card">{figures_html[2]}</div>
    <div class="card">{figures_html[3]}</div>
    <div class="card">{figures_html[4]}</div>
    <div class="card wide">{figures_html[5]}</div>
  </div>

  <div class="footer">Retail Sales Dashboard · Терехов Никита · 2026</div>
</body>
</html>"""

os.makedirs('output', exist_ok=True)
with open('output/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('✓ Дашборд сохранён: output/dashboard.html')
print('  Открой в браузере — все графики интерактивные (наведение, зум, фильтры)')
