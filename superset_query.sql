-- Query para analise no Superset: Receita Total e Lucro Bruto por mes e dimensoes
SELECT
    DATE_TRUNC('month', o.order_date) AS mes,
    p.category AS categoria,
    c.region AS regiao,
    c.state AS estado,
    o.channel AS canal_venda,
    SUM(oi.unit_price * oi.quantity) AS receita_total,
    SUM((oi.unit_price - oi.unit_cost) * oi.quantity) AS lucro_bruto
FROM
    core_order o
JOIN
    core_orderitem oi ON o.id = oi.order_id
JOIN
    core_product p ON oi.product_id = p.id
JOIN
    core_customer c ON o.customer_id = c.id
GROUP BY
    mes, categoria, regiao, estado, canal_venda
ORDER BY
    mes DESC, receita_total DESC;
