# Synthetic examples

These are invented records. Create an empty project folder, import orders.csv and customers.json, then try the following. Table names are derived from source filenames.

```sql
SELECT region, SUM(CAST(amount AS DECIMAL(18,2))) AS revenue
FROM orders GROUP BY region ORDER BY region
```

Expected: North 555.75; South 419.75; West 408.75. Total 1384.25 across 11 non-null amounts, 12 orders.

```sql
SELECT c.customer, COUNT(*) AS orders,
       SUM(CAST(o.amount AS DECIMAL(18,2))) AS revenue
FROM orders o JOIN customers c USING(customer_id)
GROUP BY c.customer ORDER BY c.customer
```

```sql
PIVOT orders ON region USING SUM(CAST(amount AS DECIMAL(18,2))) GROUP BY status
```

Profiles count NULL as missing; empty strings and literal NULL text are distinct according to import parsing. CSV type inference is automatic unless Keep CSV columns as text is selected. Use TRY_CAST in a visible query for explicit type/date handling; ambiguous dates should stay as text.
