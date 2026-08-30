create database Ecommerce_Analytics;
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
ALTER COLUMN order_id BIGINT;

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
SELECT  'website_sessions'as table_name,MIN(created_at) AS min_date, MAX(created_at) AS max_date FROM website_sessions
UNION ALL SELECT 'orders', MIN(created_at), MAX(created_at) FROM orders
UNION ALL SELECT 'order_item_refunds', MIN(created_at), MAX(created_at) FROM order_item_refunds;

-- negative reviews
select * from orders where price_usd<0

--negative cogs
select * from orders where cogs_usd<0

-- checking for logical financial relationship
select * from orders
where price_usd<cogs_usd

-- for further dates 
select * from orders 
where created_at < GETDATE()

--find extra spaces
select product_name from products
where product_name like ' %' or product_name like '% '

-- check column completeness(see how many rows are missing per column)
select count(*) as total_rows,
    count(device_type) as non_null_rows,
    count(*)-count(device_type) as null_rows
from website_sessions

select count(*) as total_rows,
    count(price_usd) as non_null_rows,
    count(*)-count(price_usd) as null_rows
from orders

select count(*) as total_rows,
    count(created_at) as non_null_rows,
    count(*)-count(created_at) as null_rows
from orders_items

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
having count(*)>1
order by cnt

--joins (when you do have two related tables) 
--Ensure Zero Orphaned Foreign Keys
--(do orders have matching session)
select count(*) as orders_without_session from orders o
left join website_sessions s on s.website_session_id =o.website_session_id
where s.website_session_id is null

--(do order_items have  matching order )
select count(*) as items_without_orders from orders_items as oi
left join orders o on o.order_id=oi.order_id
where o.order_id is null

SELECT COUNT(*) AS orphan_products FROM orders_items oi 
LEFT JOIN products p ON oi.product_id = p.product_id 
WHERE p.product_id IS NULL;

select count(*) as orphan_refund_orders from order_item_refunds r
left join orders o on o.order_id=r.order_id
where o.order_id is null

select count(*) as orphan_refund_items from order_item_refunds r
left join orders_items oi on oi.order_item_id=r.order_item_id
where oi.order_item_id is null

select count(*) as orphan_pagereviews from website_pageviews wp
left join website_sessions s on wp.website_session_id= s.website_session_id
where s.website_session_id is null

-- new product analysis
select product_id,product_name,created_at as launch_date from products
order by launch_date

--  overall number :total session/orders/revenue/conversion  rate
select 
    (select count(*) from website_sessions) as total_session,
    (select count(*) from orders) as total_orders,
    (select sum(price_usd) from orders) as total_revenue,
    round(100.0*(select count(*) from orders)/(select count(*)
    from website_sessions),2) as conversion_rate
/*
-- or 
select
count(s.website_session_id) as total_session,
count(o.order_id) as total_orders,
sum(CAST(o.price_usd AS DECIMAL(18,2))) as total_revenue,
round(100.0*count_big(o.order_id)/count_big(s.website_session_id),2)as conversion_rate
from website_sessions s
cross join orders o
*/

-- which source brings the most sessions
select utm_source,count(*) as total_session from website_sessions
group by utm_source
order by total_session

-- which product sells the most
select p.product_name,count(*) as time_ordered from orders_items oi
join products p on p.product_id=oi.product_id
group by p.product_name
order by time_ordered desc

--how much has been refunded 
select count(*) as refund_count,
    sum(refund_amount_usd) as total_refunded
from order_item_refunds

--cleaned data
-- create view (as this doesn't change the underlying table)
-- as it gives clean,reusable,read-only layer on top of raw table -- original table remain untouched

--clean website session 
create view vw_website_sessions_clean as
select website_session_id,
    created_at,
    user_id,
    is_repeat_session,
    coalesce(utm_campaign,'none')as utm_campaign, (--COALESCE in SQL is a function used to handle NULL values. It simply returns the first non‑NULL value from a list of expressions you give it.)
    coalesce(utm_source,'direct/unknown') as utm_source,
    coalesce(device_type,'unspecified')as device_type
from website_sessions

select * from vw_website_sessions_clean

-- clean order with derived margin
create view vw_order_clean as
select order_id,
    created_at,
    website_session_id,
    user_id,
    primary_product_id,
    price_usd,
    cogs_usd,
    items_purchased,
    (price_usd-cogs_usd) as margin_usd
from orders

select * from vw_order_clean

-- clean order item joined with product name and refund flag
create view vw_clean_order_items as
select oi.order_item_id,
    oi.order_id,
    oi.product_id,
    oi.is_primary_item, --flag the main product in the order
    oi.price_usd,
    oi.cogs_usd,
    p.product_name,
    isnull (r.refund_amount_usd,0) as refund_amound_usd, -- if refund exist show its amount if not(null) replace with 0
    case when r.order_item_id is not null then 1 else 0 end as is_refunded --creates a flag column 1-refunded,0-non refunded
from orders_items as oi
join products p
    on p.product_id=oi.product_id
left join order_item_refunds r
    on r.order_item_id=oi.order_item_id

select * from vw_clean_order_items

-- Session-to-Order Conversion Summary View
create view vw_session_order_summary as
select 
   s.website_session_id,
   s.created_at as session_date,
   s.utm_campaign,
   s.utm_source,
   s.device_type,
   o.order_id,
   o.price_usd,
   o.cogs_usd,
   case when o.order_id is not null then 1 else 0 end as converted
from vw_website_sessions_clean s
left join vw_order_clean o
    on o.website_session_id=s.website_session_id
select* from vw_session_order_summary

--kpi
-- monthly sessions,order,revenue,conversion rate,aov(average order value)
select year(s.created_at) as yrs,
month(s.created_at) as months,
count(distinct s.website_session_id) as sessions,
count(distinct o.order_id) as total_order,
sum( o.price_usd) as total_revenue,
round(100.0*count(distinct o.order_id)/count(distinct s.website_session_id),2) as conversion_rate_pct,
round(sum(o.price_usd)*1.0/nullif(count(distinct o.order_id),0),2) as AOV 
from website_sessions s
left join orders o
on o.website_session_id=s.website_session_id
group by year(s.created_at),month(s.created_at)
order by yrs,months

-- refund rate 
select 
count(distinct r.order_item_id) as refund_item,
count(distinct oi.order_item_id) as total_item,
round(100.0*count(distinct r.order_item_id)/count(distinct oi.order_item_id),2) as refund_rate
from orders_items oi 
left join order_item_refunds r
on r.order_item_id=oi.order_item_id

--product mix- revenue and % share per product  
select 
p.product_name,
count(distinct oi.order_id) as orders,
sum(oi.price_usd) as revenue, -- total revenue 
round(100.0*sum(oi.price_usd)/sum(sum(oi.price_usd)) over(),2) as pct_of_total_revenue -- window function
from products p 
join orders_items oi 
on p.product_id=oi.product_id
where oi.is_primary_item=1
group by p.product_name
order by revenue desc

--campaign/source(channel)/device type 
select 
  s.utm_campaign , --COALESCE in SQL is a function used to handle NULL values. It simply returns the first non‑NULL value from a list of expressions you give it.
  s.utm_source,
  s.device_type,
  count(distinct s.website_session_id) as sessions,
  count(distinct o.order_id) as orders,
  sum(o.price_usd) as revenue,
  round(100.0*count(distinct o.order_id)/count(distinct s.website_session_id),2) as converstion_rate 
from website_sessions s 
left join orders o on o.website_session_id=s.website_session_id
group by  s.utm_campaign,s.utm_source,
  s.device_type
order by revenue

-- orders per product per month 
select 
year(o.created_at) as years,
month(o.created_at) as months,
p.product_name ,
count(distinct o.order_id) as orders 
from orders_items oi 
join orders o on o.order_id=oi.order_id
join products p on p.product_id=oi.product_id
where oi.is_primary_item=1
group by year(o.created_at) ,
month(o.created_at) ,
p.product_name
order by years,months,p.product_name

-- refund rate by product 
select 
p.product_name,
count(distinct oi.order_item_id) as item_sold,
count(distinct r.order_item_id) as refunded_items,
round(100.0*count(distinct r.order_item_id)/count(distinct oi.order_item_id),2) as refunded_rate
from orders_items oi
join products p on p.product_id=oi.product_id
left join order_item_refunds r on r.order_id=oi.order_id
group by p.product_name
order by refunded_rate desc

UPDATE website_sessions SET device_type = LTRIM(RTRIM(device_type));
select top 5 * from website_sessions

UPDATE products SET product_name = LTRIM(RTRIM(product_name));
select top 5 * from products

UPDATE website_sessions SET utm_source = LOWER(LTRIM(RTRIM(utm_source)));

SELECT COUNT(*) AS both_null_rows
FROM website_sessions
WHERE utm_source IS NULL AND http_referer IS NULL;