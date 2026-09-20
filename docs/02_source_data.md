# 02. Источник данных

## 2.1. Общее описание

| Параметр | Значение |
|---|---|
| Файл | sales.csv |
| Формат | CSV, разделитель запятая, заголовок в первой строке |
| Строк | 1000 |
| Полей | 17 |
| Период | 01.01.2019 — 30.03.2019 |
| Города | Yangon, Mandalay, Naypyitaw (Мьянма) |
| Филиалы | A, B, C |

## 2.2. Описание полей

| № | Поле | Тип | Nullable | Описание |
|---|---|---|---|---|
| 1 | Invoice ID | string | нет | Уникальный идентификатор чека |
| 2 | Branch | string | нет | Код филиала (A/B/C) |
| 3 | City | string | нет | Город |
| 4 | Customer type | string | нет | Member / Normal |
| 5 | Gender | string | нет | Male / Female |
| 6 | Product line | string | нет | Категория товара |
| 7 | Unit price | float | нет | Цена за единицу |
| 8 | Quantity | int | нет | Количество |
| 9 | Tax 5% | float | нет | Сумма налога 5% |
| 10 | Total | float | нет | Итоговая сумма с налогом |
| 11 | Date | date | нет | Дата продажи (M/D/YYYY) |
| 12 | Time | time | нет | Время (HH:MM) |
| 13 | Payment | string | нет | Cash / Credit card / Ewallet |
| 14 | cogs | float | нет | Себестоимость |
| 15 | gross margin percentage | float | нет | Маржа в % (константа 4.7619) |
| 16 | gross income | float | нет | Валовый доход = Tax 5% |
| 17 | Rating | float | да | Оценка клиента (4.0 — 10.0) |

## 2.3. Выявленные закономерности

1. Branch ↔ City — 1:1: A→Yangon, B→Mandalay, C→Naypyitaw.
2. Total = cogs + Tax 5% для всех строк.
3. gross income = Tax 5% для всех строк.
4. Tax 5% = cogs × 0.05 с точностью 0.01.
5. gross margin percentage — константа 4.7619 (100/21).
6. Invoice ID — уникальный ключ (проверено: 1000 уникальных).

## 2.4. Правила качества исходных данных

| Правило | Действие при нарушении |
|---|---|
| invoice_id NOT NULL | reject |
| invoice_id уникален | drop duplicate |
| quantity > 0 | reject |
| tax_5pct = cogs × 0.05 (±0.01) | warning |
| total = cogs + tax_5pct (±0.01) | warning |
| rating в диапазоне [0, 10] | reject |

## 2.5. Известные ограничения

- Нет суррогатного ID клиента — клиент идентифицируется парой
  (customer_type, gender).
- Нет ID продукта — товар определяется product_line (6 категорий).
- Нет явной связи чека и товара (один чек = одна позиция).
