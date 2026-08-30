create database Ecommerce_Analytics_project;
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

-- Row counts per table 
SELECT 'orders' AS table_name, COUNT(*) AS row_count FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM orders_items
UNION ALL
SELECT 'order_item_refunds', COUNT(*) FROM order_item_refunds
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'website_sessions', COUNT(*) FROM website_sessions
UNION ALL
SELECT 'website_pageviews', COUNT(*) FROM website_pageviews;

-- Date range coverage per table
SELECT 'order' as table_name, MIN(created_at) AS earliest, MAX(created_at) AS latest FROM orders
union all
SELECT 'website_session',MIN(created_at) AS earliest, MAX(created_at) AS latest FROM website_sessions
union all
SELECT 'website_pageview',MIN(created_at) AS earliest, MAX(created_at) AS latest FROM website_pageviews;

-- NULL audit — orders
SELECT
  SUM(CASE WHEN website_session_id IS NULL THEN 1 ELSE 0 END) AS null_session_id,
  SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END)             AS null_user_id,
  SUM(CASE WHEN primary_product_id IS NULL THEN 1 ELSE 0 END)  AS null_primary_product,
  SUM(CASE WHEN items_purchased IS NULL THEN 1 ELSE 0 END)     AS null_items_purchased,
  SUM(CASE WHEN price_usd IS NULL THEN 1 ELSE 0 END)           AS null_price,
  SUM(CASE WHEN cogs_usd IS NULL THEN 1 ELSE 0 END)            AS null_cogs,
  COUNT(*) AS total_rows
FROM orders;

--NULL audit — order_items
SELECT
  SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END)      AS null_order_id,
  SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END)    AS null_product_id,
  SUM(CASE WHEN is_primary_item IS NULL THEN 1 ELSE 0 END) AS null_is_primary,
  SUM(CASE WHEN price_usd IS NULL THEN 1 ELSE 0 END)     AS null_price,
  SUM(CASE WHEN cogs_usd IS NULL THEN 1 ELSE 0 END)      AS null_cogs,
  COUNT(*) AS total_rows
FROM orders_items;

--NULL audit — order_item_refunds
SELECT
  SUM(CASE WHEN order_item_id IS NULL THEN 1 ELSE 0 END)   AS null_order_item_id,
  SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END)        AS null_order_id,
  SUM(CASE WHEN refund_amount_usd IS NULL THEN 1 ELSE 0 END) AS null_refund_amount,
  COUNT(*) AS total_rows
FROM order_item_refunds;

--NULL audit — products
SELECT
  SUM(CASE WHEN product_name IS NULL THEN 1 ELSE 0 END) AS null_product_name,
  COUNT(*) AS total_rows
FROM products;

--NULL audit — website_sessions
SELECT
  SUM(CASE WHEN utm_source = 'NULL' THEN 1 ELSE 0 END)   AS null_utm_source,
  SUM(CASE WHEN utm_campaign = 'NULL' THEN 1 ELSE 0 END) AS null_utm_campaign,
  SUM(CASE WHEN utm_content = 'NULL' THEN 1 ELSE 0 END)  AS null_utm_content,
  SUM(CASE WHEN http_referer = 'NULL' THEN 1 ELSE 0 END) AS null_http_referer,
  COUNT(*) AS total_rows
FROM website_sessions;

--NULL audit — website_pageviews
SELECT
  SUM(CASE WHEN website_session_id IS NULL THEN 1 ELSE 0 END) AS null_session_id,
  SUM(CASE WHEN pageview_url IS NULL THEN 1 ELSE 0 END)       AS null_pageview_url,
  COUNT(*) AS total_rows
FROM website_pageviews;

-- distinct values 
select count(distinct order_id)as distinct_orders from orders
select count(distinct user_id) as distinct_users from orders
select count(distinct product_id) as distinct_products_sold from orders_items
select count(distinct device_type) as distinct_device,count(distinct utm_source) as distinct_utm from website_sessions

-- category value check 
select distinct  device_type from website_sessions
select distinct utm_source from website_sessions
select distinct utm_campaign from website_sessions
select distinct http_referer from website_sessions
select distinct pageview_url from website_pageviews order by 1

-- numeric range check 
select min(price_usd) as min_price,max(price_usd) as max_price,avg(price_usd) as avg_price, 
min(cogs_usd) as min_cost,max(cogs_usd) as max_cost,avg(cogs_usd) as avg_cost from orders 

select min(items_purchased) as min_purchase,max(items_purchased) as max_purchase, avg(items_purchased) as avg_purchase from orders

select min(refund_amount_usd) as min_refund,max(refund_amount_usd) as max_refund,avg(refund_amount_usd) as avg_refund from order_item_refunds

select min(price_usd) as min_price,max(price_usd) as max_price,avg(price_usd) as avg_price, 
min(cogs_usd) as min_cost,max(cogs_usd) as max_cost,avg(cogs_usd) as avg_cost from orders_items

-- data cleaning 
--  duplicate check -orders (order id should be unique)
select order_id,count(*) as cnt from orders
group by order_id
having COUNT(*)>1

--  duplicate check -order_items (order item id should be unique)
select order_item_id,count(*) as cnt from orders_items
group by order_item_id
having COUNT(*)>1

--  duplicate check -website session ( website session id should be unique)
select website_session_id,count(*) as cnt from website_sessions
group by website_session_id
having COUNT(*)>1

-- orphaned records 
-- refrential integrity - order items pointing to orders tht doesn't exist 
select oi.order_id from orders_items as oi
left join orders as o on oi.order_id=o.order_id
where o.order_id is null
-- Result: blank (no orphaned rows) — every order_items row has a valid matching order_id in orders. Referential integrity confirmed, no cleaning needed.

-- Referential integrity — orders pointing to sessions that don't exist
select o.website_session_id from orders as o
left join website_sessions as ws on o.website_session_id=ws.website_session_id
where ws.website_session_id is null
-- Result: blank (no orphaned rows) — every orders row has a valid matching website_session_id in website_ssession. Referential integrity confirmed, no cleaning needed.

--Referential integrity — order_items pointing to products that don't exist
SELECT oi.product_id
FROM orders_items oi
LEFT JOIN products p ON oi.product_id = p.product_id
WHERE p.product_id IS NULL;
-- Result: blank (no orphaned rows) — every order_items row has a valid matching product_id in products. Referential integrity confirmed, no cleaning needed.

--Refrential integrity - refund pointing to order_items that don'exist
select r.order_item_id from order_item_refunds as r
left join orders_items oi on oi.order_item_id=r.order_item_id
where oi.order_item_id is null
-- Result: blank (no orphaned rows) — every order_item_refunds row has a valid matching order_item_id in order_items. Referential integrity confirmed, no cleaning needed.

--Referential integrity — pageviews pointing to sessions that don't exist
SELECT pv.website_session_id
FROM website_pageviews pv
LEFT JOIN website_sessions ws ON pv.website_session_id = ws.website_session_id
WHERE ws.website_session_id IS NULL;
-- Result: blank (no orphaned rows) — every website_pageviews row has a valid matching website_session_id in website_session. Referential integrity confirmed, no cleaning needed.

-- invalid/out-of range values- negative or zero price ,cogs>price
select * from orders_items where price_usd<=0 or cogs_usd<0
select * from orders where price_usd<cogs_usd 
-- Result: blank for both — no invalid/negative prices in order_items, and no order sells below cost (price_usd >= cogs_usd for all orders). No cleaning needed.

-- invalid quantities 
select * from orders where items_purchased<=0
-- Result: blank — no orders with zero or negative items_purchased. Quantity data is valid, no cleaning needed.

-- refund date earlier than order date 
select r.order_item_refund_id,r.created_at as refund_date,oi.created_at as order_date from order_item_refunds r
join orders_items oi on oi.order_item_id=r.order_item_id
where r.created_at<oi.created_at
-- Result: blank — no refund_date earlier than order_date. Refund sequencing is valid, no cleaning needed.

-- refund amount exceeds original item price 
select r.order_item_refund_id,r.refund_amount_usd as refund_date,oi.price_usd as order_date from order_item_refunds r
join orders_items oi on oi.order_item_id=r.order_item_id
where r.refund_amount_usd>oi.price_usd
-- Result: blank — no refund_amount_usd exceeds the original item's price_usd. Refund amounts are valid, no cleaning needed.

-- date range sanity-no future dates or pre launch dates 
select * from orders where created_at>GETDATE()
select * from website_sessions where created_at>GETDATE()
select * from  website_pageviews where created_at>GETDATE()
-- Result: blank for all three tables — no future-dated records in created_at. Date data is valid, no cleaning needed.

--crosstable consistency-order items rows per order vs order item purchased 
select o.order_id,o.items_purchased,count(oi.order_item_id) as actual_item_rows from orders o
join orders_items oi on o.order_id=oi.order_id
group by o.order_id,o.items_purchased
having o.items_purchased <> count(oi.order_item_id)
-- Results: orders where the header count disagrees with the item-level detail

--cross table consistency-order.price_usd vs sum of order_items.price_usd
select o.order_id,o.price_usd as Total_orders,sum(oi.price_usd) as total_items from orders  o
join orders_items oi  on o.order_id=oi.order_id
group by o.order_id,o.price_usd
having o.price_usd <> sum(oi.price_usd)

-- how many can be filled from http_referer vs how many are both NULL
SELECT 
  COUNT(*) AS total_rows,
  SUM(CASE WHEN utm_source ='Null' THEN 1 ELSE 0 END) AS null_utm,
  SUM(CASE WHEN utm_source ='Null' AND http_referer IS NOT NULL THEN 1 ELSE 0 END) AS fillable_from_ref,
  SUM(CASE WHEN utm_source ='Null' AND http_referer ='Null' THEN 1 ELSE 0 END) AS both_null
FROM website_sessions;

-- fix literal 'null' text -> convert to true null 
UPDATE website_sessions SET utm_source = NULL WHERE utm_source = 'NULL';
UPDATE website_sessions SET utm_campaign = NULL WHERE utm_campaign = 'NULL';
UPDATE website_sessions SET utm_content = NULL WHERE utm_content = 'NULL';
UPDATE website_sessions SET http_referer = NULL WHERE http_referer = 'NULL';
-- Purpose: makes IS NULL / ISNULL() / aggregate functions behave correctly on these columns going forward

-- fill utm_source 

UPDATE website_sessions
SET utm_source = 'unknown'
WHERE utm_source IS NULL;

SELECT * FROM website_sessions;

SELECT COUNT(*) AS remaining_nulls FROM website_sessions
WHERE utm_source IS NULL;

SELECT DISTINCT utm_source FROM website_sessions
ORDER BY utm_source;
--------
UPDATE website_sessions
SET utm_campaign = 'unknown'
WHERE utm_campaign IS NULL;

SELECT COUNT(*) AS remaining_nulls FROM website_sessions
WHERE utm_campaign IS NULL;

SELECT DISTINCT utm_campaign FROM website_sessions
ORDER BY utm_campaign;
---------
update website_sessions
set utm_content='unknown'
where  utm_content is null;

SELECT COUNT(*) AS remaining_nulls FROM website_sessions
WHERE utm_content IS NULL;

SELECT DISTINCT utm_content FROM website_sessions
ORDER BY utm_content;
--------
update website_sessions
set http_referer='unknown'
where http_referer is null;

SELECT COUNT(*) AS remaining_nulls FROM website_sessions
WHERE http_referer IS NULL;

SELECT DISTINCT http_referer FROM website_sessions
ORDER BY http_referer;

-- KPI Definitions
--- total revenue
select sum(price_usd) as total_revenue from orders_items

-- total refunds
select sum(refund_amount_usd) as total_refund from order_item_refunds

-- net revenue (revenue-refund)
select 
	(select sum(price_usd) from orders_items)-
	(select sum(refund_amount_usd) from order_item_refunds) as net_revenue

-- gross margin (revenue minus cost of good sold)
 select 
	sum(price_usd) as revenue,
	sum(cogs_usd) as total_cogs,
	sum(price_usd)-sum(cogs_usd) as gross_margin,
	(sum(price_usd)-sum(cogs_usd))*100.0/sum(price_usd) as gross_margin_pct
from orders_items

-- average order value 
select sum(price_usd)*1.0/count(distinct order_id) as avg_order_value from orders

-- total session and total orders 
select 
	(select count(*) from website_sessions) as total_sessions,
	(select count(*) from orders ) as total_orders

-- session to order conversion rate
select count(distinct o.order_id)*1.0/count(distinct ws.website_session_id) as conversion_rate
from website_sessions ws
left join orders o on ws.website_session_id=o.website_session_id

-- repeat session rate
select 
	sum(case when is_repeat_session=1 then 1 else 0 end)*1.0/count(*) as repeat_session_rate
from  website_sessions

-- revenue by channel 
select ws.utm_source,
	count(distinct o.order_id) as orders,
	sum(oi.price_usd) as revenue
	from website_sessions ws
join orders o on ws.website_session_id=o.website_session_id
join orders_items oi on oi.order_id=o.order_id
group by ws.utm_source
order by revenue desc

-- revenue by device_type 
select ws.device_type,
	count(distinct o.order_id) as orders,
	sum(oi.price_usd) as revenue
	from website_sessions ws
join orders o on ws.website_session_id=o.website_session_id
join orders_items oi on oi.order_id=o.order_id
group by ws.device_type
order by revenue desc

-- refund rate (refunnd items/ total item sold)
select count(distinct r.order_item_id)*1.0/count(distinct oi.order_item_id) as refund_rate
from orders_items oi
left join order_item_refunds r on r.order_item_id=oi.order_item_id

-- revenue per product  
select p.product_name,COUNT(distinct oi.order_item_id) as units_sold,sum(oi.price_usd)as revenue
from orders_items oi 
join products p on p.product_id=oi.product_id
group by p.product_name
order by revenue desc

-- other exploratory analysis
-- monthly revenue trend  
select format (created_at,'yyyy-MM') as month,
	sum(price_usd) as revenue
from orders_items 
group by format (created_at,'yyyy-MM')
order by month desc

-- monthly session trend
select format (created_at,'yyyy-MM') as month,
	count(*) as session
from website_sessions
group by format (created_at,'yyyy-MM')
order by month desc

-- most viewed page 
select top 10 pageview_url,count(*) as views
from website_pageviews
group by pageview_url
order by views

-- top campaign by session
select utm_campaign,count(*) as sessions from website_sessions
group by utm_campaign
order by sessions

-- primary item vs add on items
select is_primary_item,count(*) as item_count,sum(price_usd) as revenue from orders_items
group by is_primary_item

-- post clean validation 
-- re-run row count after cleaning 
SELECT 'orders' AS table_name, COUNT(*) AS row_count FROM orders
UNION ALL
SELECT 'orders_items', COUNT(*) FROM orders_items
UNION ALL
SELECT 'order_item_refunds', COUNT(*) FROM order_item_refunds;

-- re run null audit on key join columns to confirm zero null
SELECT
  SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) AS null_order_id,
  SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_product_id,
FROM orders_items;

-- confirm website session null fix worked 
select 
	sum(case when utm_source is null then 1 else 0 end) as null_utm_source,
	count(*) as total_rows
from website_sessions