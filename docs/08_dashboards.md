# 08. Дашборды Tableau

## 8.1. Подключение к данным

Используется Tableau Public Online (public.tableau.com).
Источник — CSV-файлы, выгруженные из DDS:

- tableau/fact_sales_full.csv — 1000 строк, 15 полей (главный источник)
- tableau/sales_by_product.csv
- tableau/sales_by_branch.csv
- tableau/payment_customer.csv
- tableau/time_patterns.csv

Альтернатива: подключение напрямую к PostgreSQL (БД dwh, user airflow).

## 8.2. Листы дашборда

### Лист 1: Revenue by Product
- Тип: горизонтальный Bar chart
- Rows: product_line_name
- Columns: SUM(total)
- Label: SUM(total)
- Сортировка: по убыванию
- Insight: лидирует Food and beverages (56 145), отстаёт Health and beauty (49 194).

### Лист 2: KPI Total Revenue
- Тип: текстовая карточка
- Text: SUM(total)
- Значение: 322 967

### Лист 3: Revenue by City
- Тип: вертикальный Bar chart
- Columns: city
- Rows: SUM(total)
- Color: branch_code
- Insight: Naypyitaw лидирует (110 569), Yangon и Mandalay близки (~106 200).

### Лист 4: Payment Share
- Тип: Pie chart
- Color: payment_name
- Angle: SUM(total)
- Insight: три способа оплаты распределены равномерно.

### Лист 5: Monthly Trend
- Тип: Line chart
- Columns: full_date (Month)
- Rows: SUM(total)
- Color: city
- Insight: пик продаж — в январе и марте 2019.

### Лист 6: Heatmap Day Part × Weekday
- Тип: Heatmap
- Rows: day_part
- Columns: full_date (Weekday)
- Color: SUM(total)
- Insight: пики продаж — вечером и по выходным.

## 8.3. Итоговый дашборд

Компоновка (сетка 12 × 3):

| Позиция | Лист |
|---|---|
| Верх (весь ряд) | KPI Total Revenue |
| 2-й ряд, левая половина | Revenue by Product |
| 2-й ряд, правая половина | Revenue by City |
| 3-й ряд, левая половина | Payment Share |
| 3-й ряд, правая половина | Heatmap |

Размер: Desktop Browser (1000 × 800).

## 8.4. Публикация

Workbook сохранён на public.tableau.com:
- Название: diploma_sales_dashboard
- Ссылка: https://public.tableau.com/views/dhdash/Dashboard1
- Файл .twbx для сдачи: доступен по публичной ссылке (кнопка Download на странице Tableau Public)

## 8.5. Скриншоты

См. docs/img/:
- dashboard_overview.png — итоговый дашборд
- sheet_product.png — Revenue by Product
- sheet_city.png — Revenue by City
- sheet_payment.png — Payment Share