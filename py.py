import pandas as pd
import json

# 1. ЗАГРУЗКА И ПОДГОТОВКА ДАННЫХ
df = pd.read_csv('./data/marketing_campaign.csv', sep='\t')

# Нормализация категорий
df["Education"] = df["Education"].replace({"2n Cycle": "Pre-Graduate", "Basic": "Pre-Graduate"})
df["Marital_Status"] = df["Marital_Status"].replace({
    "Married": "Married/Together", "Together": "Married/Together",
    "Single": "Single", "Divorced": "Other", "Widow": "Other",
    "Alone": "Other", "Absurd": "Other", "YOLO": "Other"
})

# Вычисляемые столбцы
df['Age'] = 2024 - df['Year_Birth']  
df['Total_Children'] = df['Kidhome'] + df['Teenhome']  
df['Has_Children'] = df['Total_Children'].apply(lambda x: 'Да' if x > 0 else 'Нет')
df['Total_Spending'] = df[['MntWines', 'MntFruits', 'MntMeatProducts', 
                           'MntFishProducts', 'MntSweetProducts', 'MntGoldProds']].sum(axis=1) 

# Очистка
df['Income'] = df['Income'].fillna(df['Income'].median())
df = df[df['Income'] < 200000]

# Подготовка JSON
cols_to_save = [
    'Education', 'Marital_Status', 'Has_Children', 'Income', 'Total_Spending', 'Age',
    'MntWines', 'MntFruits', 'MntMeatProducts', 'MntFishProducts', 'MntSweetProducts', 'MntGoldProds',
    'NumWebPurchases', 'NumCatalogPurchases', 'NumStorePurchases', 'NumDealsPurchases',
    'AcceptedCmp1', 'AcceptedCmp2', 'AcceptedCmp3', 'AcceptedCmp4', 'AcceptedCmp5', 'Response'
]
data_json = df[cols_to_save].to_json(orient='records')

# ГЕНЕРИРУЕМ ОПЦИИ ДЛЯ ФИЛЬТРОВ ЗАРАНЕЕ (исправление ошибки {o})
edu_options = sorted(df['Education'].unique().tolist())
marital_options = sorted(df['Marital_Status'].unique().tolist())

edu_html_options = "".join([f'<option value="{opt}">{opt}</option>' for opt in edu_options])
marital_html_options = "".join([f'<option value="{opt}">{opt}</option>' for opt in marital_options])

# 2. ШАБЛОН HTML
html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Marketing Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #f1f3f6; font-family: 'Segoe UI', sans-serif; }}
        .header-box {{ background: #2c3e50; color: white; padding: 20px; margin-bottom: 20px; border-radius: 0 0 15px 15px; }}
        .card {{ border: none; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
        .filter-label {{ font-weight: 600; color: #444; font-size: 0.9rem; }}
        .kpi-title {{ color: #7f8c8d; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }}
        .kpi-value {{ font-size: 1.8rem; font-weight: bold; color: #2c3e50; }}
        .chart-title {{ padding: 15px 0 0 15px; font-weight: bold; color: #34495e; }}
    </style>
</head>
<body>

<div class="header-box text-center">
    <h1>Маркетинговый дашборд</h1>
    <p>Анализ сегментов и поведения клиентов</p>
</div>

<div class="container-fluid px-4">
    <div class="card p-3 mb-4">
        <div class="row align-items-center">
            <div class="col-md-3">
                <label class="filter-label">1. Образование</label>
                <select id="eduFilter" class="form-select" onchange="refresh()">
                    <option value="All">Все категории</option>
                    {edu_html_options}
                </select>
            </div>
            <div class="col-md-3">
                <label class="filter-label">2. Семейное положение</label>
                <select id="maritalFilter" class="form-select" onchange="refresh()">
                    <option value="All">Все статусы</option>
                    {marital_html_options}
                </select>
            </div>
            <div class="col-md-3">
                <label class="filter-label">3. Наличие детей</label>
                <select id="kidsFilter" class="form-select" onchange="refresh()">
                    <option value="All">Неважно</option>
                    <option value="Да">Есть дети</option>
                    <option value="Нет">Нет детей</option>
                </select>
            </div>
            <div class="col-md-3 text-center">
                <div class="kpi-title">Выбрано клиентов</div>
                <div id="countKPI" class="kpi-value">0</div>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-md-4"><div class="card p-3 text-center"><div class="kpi-title">Средний чек</div><div id="spendingKPI" class="kpi-value" style="color: #e67e22;">$0</div></div></div>
        <div class="col-md-4"><div class="card p-3 text-center"><div class="kpi-title">Средний годовой доход</div><div id="incomeKPI" class="kpi-value" style="color: #27ae60;">$0</div></div></div>
        <div class="col-md-4"><div class="card p-3 text-center"><div class="kpi-title">Средний возраст</div><div id="ageKPI" class="kpi-value" style="color: #2980b9;">0</div></div></div>
    </div>

    <div class="row">
        <div class="col-md-8"><div class="card"><div class="chart-title">Доход vs Траты</div><div id="scatterChart" style="height: 450px;"></div></div></div>
        <div class="col-md-4"><div class="card"><div class="chart-title">Состав корзины</div><div id="donutChart" style="height: 450px;"></div></div></div>
    </div>

    <div class="row">
        <div class="col-md-6"><div class="card"><div class="chart-title">Каналы продаж</div><div id="channelsChart" style="height: 350px;"></div></div></div>
        <div class="col-md-6"><div class="card"><div class="chart-title">Маркетинговые кампании</div><div id="campaignsChart" style="height: 350px;"></div></div></div>
    </div>
</div>

<script>
    const rawData = {data_json};

    function refresh() {{
        const edu = document.getElementById('eduFilter').value;
        const marital = document.getElementById('maritalFilter').value;
        const kids = document.getElementById('kidsFilter').value;

        const filtered = rawData.filter(d => {{
            return (edu === 'All' || d.Education === edu) &&
                   (marital === 'All' || d.Marital_Status === marital) &&
                   (kids === 'All' || d.Has_Children === kids);
        }});

        if (filtered.length === 0) {{
             alert("Данные не найдены!");
             return;
        }}

        const avgSpending = filtered.reduce((a, b) => a + b.Total_Spending, 0) / filtered.length;
        const avgIncome = filtered.reduce((a, b) => a + b.Income, 0) / filtered.length;
        const avgAge = filtered.reduce((a, b) => a + b.Age, 0) / filtered.length;

        document.getElementById('countKPI').innerText = filtered.length;
        document.getElementById('spendingKPI').innerText = '$' + Math.round(avgSpending).toLocaleString();
        document.getElementById('incomeKPI').innerText = '$' + Math.round(avgIncome).toLocaleString();
        document.getElementById('ageKPI').innerText = Math.round(avgAge);

        // 1. Scatter
        Plotly.react('scatterChart', [{{
            x: filtered.map(d => d.Income),
            y: filtered.map(d => d.Total_Spending),
            mode: 'markers',
            marker: {{ color: filtered.map(d => d.Response === 1 ? '#1abc9c' : '#34495e'), opacity: 0.6 }},
            type: 'scatter'
        }}], {{ xaxis: {{title: 'Доход'}}, yaxis: {{title: 'Траты'}} }});

        // 2. Donut
        const products = ['Вино', 'Фрукты', 'Мясо', 'Рыба', 'Сладости', 'Золото'];
        const prodKeys = ['MntWines', 'MntFruits', 'MntMeatProducts', 'MntFishProducts', 'MntSweetProducts', 'MntGoldProds'];
        Plotly.react('donutChart', [{{
            values: prodKeys.map(k => filtered.reduce((a, b) => a + b[k], 0)),
            labels: products,
            type: 'pie', hole: 0.5
        }}], {{ showlegend: true, legend: {{orientation: 'h'}} }});

        // 3. Channels
        Plotly.react('channelsChart', [{{
            x: ['Веб', 'Каталог', 'Магазин', 'Скидки'],
            y: ['NumWebPurchases', 'NumCatalogPurchases', 'NumStorePurchases', 'NumDealsPurchases'].map(k => filtered.reduce((a, b) => a + b[k], 0) / filtered.length),
            type: 'bar', marker: {{color: '#34495e'}}
        }}]);

        // 4. Campaigns
        Plotly.react('campaignsChart', [{{
            x: ['Cmp 1', 'Cmp 2', 'Cmp 3', 'Cmp 4', 'Cmp 5'],
            y: ['AcceptedCmp1', 'AcceptedCmp2', 'AcceptedCmp3', 'AcceptedCmp4', 'AcceptedCmp5'].map(k => filtered.reduce((a, b) => a + b[k], 0)),
            type: 'bar', marker: {{color: '#9b59b6'}}
        }}]);
    }}
    refresh();
</script>
</body>
</html>
"""

with open("marketing_dashboard_final.html", "w", encoding="utf-8") as f:
    f.write(html_content)
print("Готово! Обновите файл.")