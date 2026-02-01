-- Query para análise no Superset: Receita Total e Lucro Bruto por mês e dimensões
SELECT
    DATE_TRUNC('month', o.created_at) AS mes,
    p.category AS categoria,
    c.region AS regiao,
    c.state AS estado,
    o.sales_channel AS canal_venda,
    SUM(oi.price * oi.quantity) AS receita_total,
    SUM((oi.price - oi.cost) * oi.quantity) AS lucro_bruto
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