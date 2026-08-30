create database EcommerceAnalytics;
select * from order_item_refunds
select *from orders_items
select * from orders
select * from products
select * from website_pageviews
select * from website_sessions

SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

-- schema/keys
-- foreign keys 
alter table	website_pageviews 
	add CONSTRAINT FK_pageviews_sessions
	foreign key (website_session_id) references website_sessions(website_session_id)

alter table	orders 
	add CONSTRAINT FK_orders_sessions
	foreign key (website_session_id) references website_sessions(website_session_id)

ALTER TABLE orders_items
    ADD CONSTRAINT FK_orders_items_orders
    FOREIGN KEY (order_id) REFERENCES orders(order_id);

ALTER TABLE orders_items
ADD CONSTRAINT fk_product_orders_item
FOREIGN KEY (product_id) REFERENCES products(product_id);
 
ALTER TABLE order_item_refunds
    ADD CONSTRAINT FK_refunds_orders_items
    FOREIGN KEY (order_item_id) REFERENCES orders_items(order_item_id);
 
ALTER TABLE order_item_refunds
    ADD CONSTRAINT FK_refunds_orders
    FOREIGN KEY (order_id) REFERENCES orders(order_id);

--How many rows in each table?
SELECT COUNT(*) FROM website_sessions;
SELECT COUNT(*) FROM website_pageviews;
SELECT COUNT(*) FROM orders;
SELECT COUNT(*) FROM orders_items;
SELECT COUNT(*) FROM order_item_refunds;
SELECT COUNT(*) FROM products;

--What does the data actually look like? 
SELECT TOP 10 * FROM website_sessions;
SELECT TOP 10 * FROM orders;
SELECT TOP 10 * FROM orders_items;
SELECT TOP 10 * FROM products;

--date range does the data cover? (-- Using UNION ALL to combine results from multiple tables without removing duplicates)
SELECT  MIN(created_at) AS min_date, MAX(created_at) AS max_date FROM website_sessions
UNION ALL SELECT 'orders', MIN(created_at), MAX(created_at) FROM orders
UNION ALL SELECT 'order_item_refunds', MIN(created_at), MAX(created_at) FROM order_item_refunds;

--Null checks on key dimension columns
SELECT
    SUM(CASE WHEN utm_source IS NULL THEN 1 ELSE 0 END)   AS null_utm_source,
    SUM(CASE WHEN utm_campaign IS NULL THEN 1 ELSE 0 END) AS null_utm_campaign,
    SUM(CASE WHEN device_type IS NULL THEN 1 ELSE 0 END)  AS null_device_type,
    COUNT(*) AS total_sessions
FROM website_sessions;

--Distinct values  (to removes duplicates from the query results)
SELECT DISTINCT utm_source FROM website_sessions ORDER BY utm_source;
SELECT DISTINCT utm_campaign FROM website_sessions ORDER BY utm_campaign;
SELECT DISTINCT device_type FROM website_sessions ORDER BY device_type;
SELECT DISTINCT product_name FROM products order by product_name;

--How many sessions/orders/revenue per month? 
SELECT
    YEAR(created_at) AS yrs,
    MONTH(created_at) AS months,
    COUNT(*) AS sessions
FROM website_sessions
GROUP BY YEAR(created_at), MONTH(created_at)
ORDER BY yrs, months;
 
SELECT
    YEAR(created_at) AS yrs,
    MONTH(created_at) AS months,
    COUNT(*) AS orders,
    SUM(price_usd) AS revenue
FROM orders
GROUP BY YEAR(created_at), MONTH(created_at)
ORDER BY yrs, months;

--Duplicate check on order_items primary key
SELECT order_item_id, COUNT(*) AS cnt
FROM orders_items
GROUP BY order_item_id
HAVING COUNT(*) > 1;

--joins 
--(do orders have matching session)
select count(*) as orders_without_session from orders o
left join website_sessions s on s.website_session_id =o.website_session_id
where s.website_session_id is null
--(do order_items have  matching order )
select count(*) as items_without_orders from orders_items as oi
left join orders o on o.order_id=oi.order_id
where o.order_id is null

DROP TABLE order_items;
