#!/usr/bin/env python
# coding: utf-8

# In[2]:


# pip install pyodbc pandas


# In[3]:


import pandas as pd
import pyodbc


# In[19]:


# connection string 
conn=pyodbc.connect(
    'Driver={SQL Server};'
    'Server=KOMAL\SQLEXPRESS;'
    'Database=Ecommerce_Analytics_project;'
    'Trusted_connection=yes;'
)
# create curson
cursor=conn.cursor()


# In[20]:


sessions = pd.read_sql("SELECT * FROM website_sessions", conn)
orders = pd.read_sql("SELECT * FROM orders", conn)
order_items = pd.read_sql("SELECT * FROM orders_items", conn)
products = pd.read_sql("SELECT * FROM products", conn)
refunds = pd.read_sql("SELECT * FROM order_item_refunds", conn)
website_pageviews = pd.read_sql("SELECT * FROM website_pageviews", conn)


# In[21]:


print(sessions.head())
print(orders.head())
print(order_items.head())
print(products.head())
print(refunds.head())
print(website_pageviews.head())


# In[64]:


# now fixing outliers  
#--orders table
for col in ['price_usd','cogs_usd','items_purchased']:
    q1=orders[col].quantile(0.25)
    q3=orders[col].quantile(0.75)
    iqr=q3-q1
    lower=max(q1-1.5*iqr,0)
    upper=q3+1.5*iqr

    flag_col=col+"_was_outlier"
    orders[flag_col]=(orders[col]<lower)|(orders[col]>upper)
    n_flagged=orders[flag_col].sum()

    orders[col]=orders[col].clip(lower=lower,upper=upper)
    print(f'orders.{col}:bounds=({lower:.2f},{upper:.2f}),{n_flagged} rows capped')
    


# In[65]:


# order_items
for col in ['price_usd','cogs_usd']:
    q1=order_items[col].quantile(0.25)
    q3=order_items[col].quantile(0.75)
    iqr=q3-q1
    lower=max(q1-1.5*iqr,0)
    upper=q3+1.5*iqr

    flag_col=col+"_was_outlier"
    order_items[flag_col]=(order_items[col]<lower)|(order_items[col]>upper)
    n_flagged=order_items[flag_col].sum()

    order_items[col]=order_items[col].clip(lower=lower,upper=upper)
    print(f'order_items.{col}:bounds=({lower:.2f},{upper:.2f}),{n_flagged} rows capped')


# In[66]:


# order item refund
col = 'refund_amount_usd'
q1=refunds[col].quantile(0.25)
q3=refunds[col].quantile(0.75)
iqr=q3-q1
lower=max(q1-1.5*iqr,0)
upper=q3+1.5*iqr

flag_col=col+"_was_outlier"
refunds[flag_col]=(refunds[col]<lower)|(refunds[col]>upper)
n_flagged=refunds[flag_col].sum()

refunds[col]=refunds[col].clip(lower=lower,upper=upper)
print(f'refunds.{col}:bounds=({lower:.2f},{upper:.2f}),{n_flagged} rows capped')

import os

os.makedirs("clean_data", exist_ok=True)

sessions.to_csv("clean_data/sessions_clean.csv", index=False)
orders.to_csv("clean_data/orders_clean.csv", index=False)
order_items.to_csv("clean_data/order_items_clean.csv", index=False)
products.to_csv("clean_data/products_clean.csv", index=False)
refunds.to_csv("clean_data/refunds_clean.csv", index=False)
website_pageviews.to_csv("clean_data/website_pageviews_clean.csv", index=False)

print("Cleaned tables exported to ./clean_data/")

# ### DESCRIPTIVE ANALYSIS (what happened)

# In[25]:


total_revenue=order_items['price_usd'].sum()
total_refund=refunds['refund_amount_usd'].sum()
net_revenue=total_revenue-total_refund


# In[26]:


total_cogs=order_items['cogs_usd'].sum()
gross_margin=total_revenue-total_cogs
gros_margin_perc=gross_margin/total_revenue*1000


# In[27]:


total_orders=orders['order_id'].nunique()
total_session=sessions['website_session_id'].nunique()
conversion_rate=total_orders/total_session*100
avg_value_order=orders['price_usd'].sum()/total_orders


# In[28]:


print('total_revenue:',round(total_revenue,2))
print('total_refund:',round(total_refund,2))
print('net_revenue:',round(net_revenue,2))
print('total_cogs:',round(total_cogs,2))
print('gross_margin:',round(gross_margin,2))
print('gros_margin_%:',round(gros_margin_perc,2))
print('conversion_rate_%:',round(conversion_rate,2))
print('total_orders:',total_revenue)
print('total_session:',total_revenue)
print('Avg order value:', round(avg_value_order, 2))


# In[29]:


# monthly sales & revenue trend 
order_items['months']=order_items['created_at'].dt.to_period('M').astype(str)
monthly_revenue=order_items.groupby('months')['price_usd'].sum().reset_index()
monthly_revenue=monthly_revenue.sort_values('months')
monthly_revenue['sales_growth']=monthly_revenue['price_usd'].pct_change()
print('\n=====monthly revenue=====')
print(monthly_revenue.to_string(index=False))


# In[30]:


# monthly session trend 
'''  Does traffic track with revenue month to month, or do they move independently'''
sessions['months']=sessions['created_at'].dt.to_period('M').astype(str)
monthly_sessions=sessions.groupby('months').size().reset_index(name='sessions')
monthly_sessions=monthly_sessions.sort_values('months')
print('\n=====monthly revenue=====')
print(monthly_sessions.to_string(index=False))

busy_month=monthly_sessions.loc[monthly_sessions['sessions'].idxmax()]
quite_month=monthly_sessions.loc[monthly_sessions['sessions'].idxmin()]
print(f"insights:{busy_month['months']} had the traffic ({busy_month['sessions']} sessions),"
      f"{quite_month['months']}had the least ({quite_month['sessions']} sessions).")


# In[31]:


#revenue by channel 
merged=sessions[['website_session_id','utm_source']].merge(orders[['order_id','website_session_id']],on='website_session_id')
merged=merged.merge(order_items[['order_id','price_usd']],on='order_id')
revenue_by_source=merged.groupby('utm_source').agg(
    orders=('order_id','nunique'),revenue=('price_usd','sum')).reset_index().sort_values('revenue',ascending=False)
print('\n======revenue by channel======')
print(revenue_by_source.to_string(index=False))


# In[33]:


import matplotlib.pyplot as plt
import seaborn as sns 
plt.figure(figsize=(8,4))
plt.bar(revenue_by_source['utm_source'],revenue_by_source['revenue'],color='orange')
plt.title('revenue_by_source')
plt.xlabel('source')
plt.ylabel('revenue')
plt.tight_layout()
plt.show()

top_source=revenue_by_source.iloc[0]
print(f"insights:{top_source['utm_source']} brings in the most revenue"
      f"({top_source['revenue']:.2f} from {top_source['orders']} orders).")


# In[34]:


#revenue by device 
merged2=sessions[['website_session_id','device_type']].merge(orders[['order_id','website_session_id']],on='website_session_id')
merged2=merged2.merge(order_items[['order_id','price_usd']],on='order_id')
revenue_by_device=merged2.groupby('device_type').agg(
    orders=('order_id','nunique'),revenue=('price_usd','sum')).reset_index().sort_values('revenue',ascending=False)
print('\n======revenue by device======')
print(revenue_by_device.to_string(index=False))


# In[35]:


plt.figure(figsize=(6,3))
plt.bar(revenue_by_device['device_type'],revenue_by_device['revenue'],color='pink')
plt.title('revenue by device')
plt.xlabel('revenue')
plt.ylabel('device types')
plt.tight_layout()
plt.show()

top_device = revenue_by_device.iloc[0]
print(f"Insight: {top_device['device_type']} generates the most revenue "
      f"({top_device['revenue']:.2f}).")


# In[36]:


#top products
merged3=order_items.merge(products,on='product_id')
top_products=merged3.groupby('product_name').agg(
    units_sold=('order_item_id','nunique'),revenue=('price_usd','sum')).reset_index().sort_values('revenue',ascending=False)
print('\n======top produts=======')
print(top_products.to_string(index=False))


# In[37]:


plt.figure(figsize=(10, 4))
plt.bar(top_products["product_name"], top_products["revenue"], color="darkorange")
plt.title("Top Products by Revenue")
plt.xlabel("Product")
plt.ylabel("Revenue (USD)")
plt.tight_layout()
plt.show()

best_product = top_products.iloc[0]
print(f"Insight: {best_product['product_name']} is the top seller "
      f"({best_product['revenue']:.2f} from {best_product['units_sold']} units).")


# In[38]:


# ordertrend match the revenue trend
order_trend=orders.groupby(orders['created_at'].dt.to_period('M')).agg(
    order_count=('order_id','nunique'),
    revenue=('price_usd','sum')
)

order_trend = order_trend.reset_index()
order_trend['created_at'] = order_trend['created_at'].astype(str)  # Period -> string for clean x-axis

order_trend

fig, ax1 = plt.subplots(figsize=(12, 5))

# Order count line (left axis)
ax1.plot(order_trend['created_at'], order_trend['order_count'], 
         color='steelblue', marker='o', label='Order Count')
ax1.set_xlabel('Month')
ax1.set_ylabel('Order Count', color='steelblue')
ax1.tick_params(axis='y', labelcolor='steelblue')
plt.xticks(rotation=45)

# Revenue line (right axis, since scale is very different)
ax2 = ax1.twinx()
ax2.plot(order_trend['created_at'], order_trend['revenue'], 
         color='darkorange', marker='o', label='Revenue')
ax2.set_ylabel('Revenue (USD)', color='darkorange')
ax2.tick_params(axis='y', labelcolor='darkorange')

plt.title('Monthly Order Count vs Revenue Trend')
fig.tight_layout()
plt.show()


# In[39]:


''' average order value trend '''
aov_trend=orders.groupby(orders['created_at'].dt.to_period('M')).agg(
    order_count=('order_id','nunique'),
    sales=('price_usd','sum')
).reset_index()
aov_trend['aov']=aov_trend['sales']/aov_trend['order_count']
aov_trend['months']=aov_trend['created_at'].astype(str)
aov_trend

plt.figure(figsize=(14,6))
sns.barplot(data=aov_trend,x='months',y='aov',color='teal')
plt.xticks(rotation=90)
plt.title('monthly aov trend',fontweight='bold',fontsize=16)
plt.tight_layout()
plt.show()


# In[40]:


# price and cost distribution (spread of the numbers,not just totals)
price_dist=order_items['price_usd'].describe()
cogs_dist=order_items['cogs_usd'].describe()
print('\n== price distribution ==')
print(price_dist.to_string())
print("\n ===== cost distribiution ======")
print(cogs_dist.to_string())

plt.figure(figsize=(8,5))
plt.hist(order_items['price_usd'],bins=20,color='pink',edgecolor='black')
plt.title('price and cost distribution')
plt.xlabel('price')
plt.ylabel('no. of order items')
plt.tight_layout()
plt.show()

print(f"insights: typical item price sits around {price_dist['50%']:.2f}(median),"
      f"ranging from ${price_dist['min']:.2f} to ${price_dist['max']:.2f}.")


# In[41]:


# revenue consistency check 
orders['years']=orders['created_at'].dt.year
orders['month_num']=orders['created_at'].dt.month
orders['quarter']=orders['created_at'].dt.quarter

heatmap_data=orders.pivot_table(
    index='years',
    columns='month_num',
    values='price_usd',
    aggfunc='sum'
)
sns.heatmap(heatmap_data,cmap='Blues')
plt.show()

quarter_data=orders.groupby(['years','quarter'])['price_usd'].sum().reset_index()
quarter_pivot=quarter_data.pivot(index='years',columns='quarter',values='price_usd')

quarter_pivot.plot(kind='bar',stacked=True)
plt.show()


# In[42]:


order_size_distribution=orders['items_purchased'].value_counts().sort_index().reset_index()
order_size_distribution.columns=['items_purchased','num_orders']
print('/n ======= order size distribution ========')
print(order_size_distribution.to_string(index=False))
plt.figure(figsize=(4,4))
plt.bar(order_size_distribution['items_purchased'].astype(str),order_size_distribution['num_orders'],color='mediumseagreen')
plt.title('order size distribution')
plt.xlabel('items per order')
plt.ylabel('number of order')
plt.tight_layout()
plt.show()
most_common_size = order_size_distribution.loc[order_size_distribution["num_orders"].idxmax()]
print(f"Insight: Most orders contain {most_common_size['items_purchased']} item(s) "
      f"({most_common_size['num_orders']} orders).")


# In[43]:


# New vs repeat visitor mix (raw counts, before tying to convers 
session_mix=sessions['is_repeat_session'].value_counts().reset_index()
session_mix.columns=['is_repeat_session','num_sessions']
session_mix['label']=session_mix['is_repeat_session'].map({0:"new",1:"repeat"})
session_mix['pct_of_sessions']=(session_mix['num_sessions']/session_mix['num_sessions'].sum()*100).round(2)
print('\n==== new vs reppeat session (visitor mix)=====')
print(session_mix[['label','pct_of_sessions','num_sessions']].to_string(index=False))
plt.figure(figsize=(5,3))
plt.pie(session_mix['num_sessions'],labels=session_mix['label'],autopct='%1.1f%%',colors=['pink','purple'])
plt.title('new vs repeat visitor mix')
plt.legend()
plt.tight_layout()
plt.show()

repeat_pct=session_mix.loc[session_mix['label']=='repeat','pct_of_sessions'].values[0]
print(f'insights:repeat  visitors make up {repeat_pct}% of all sessions.')


# In[44]:


# refund trend over time 
refunds['created_at']=pd.to_datetime(refunds['created_at'])
refunds['month']=refunds['created_at'].dt.to_period('M').astype(str)
monthly_refunds=refunds.groupby('month')['refund_amount_usd'].sum().reset_index()
monthly_refunds=monthly_refunds.sort_values('month')
print('\n====monthly refund trend=====')
print(monthly_refunds.to_string(index=False))
plt.figure(figsize=(8, 4))
plt.plot(monthly_refunds['month'],monthly_refunds['refund_amount_usd'],marker='o',color='red')
plt.title('monthly refund trend')
plt.xlabel('month')
plt.ylabel('refunds')
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()

worst_refund_month = monthly_refunds.loc[monthly_refunds["refund_amount_usd"].idxmax()]
print(f"Insight: {worst_refund_month['month']} had the highest refund total "
      f"(${worst_refund_month['refund_amount_usd']:.2f}).")


# In[45]:


#session mix by channel and device
source_mix=sessions['utm_source'].value_counts(normalize=True).round(2).reset_index()
source_mix.columns=['utm_source','pct_of_sessions']
device_mix=sessions['device_type'].value_counts(normalize=True).round(2).reset_index()
device_mix.columns=['device_type','pct_of_sessions']
print('\n=======session mix by source (% of traffic)=========')
print(source_mix.to_string(index=False))
print('\n======session mix by device=======')
print(device_mix.to_string(index=False))

plt.figure(figsize=(6,4))
plt.bar(source_mix['utm_source'],source_mix['pct_of_sessions'],color='darkgreen')
plt.title('session mix by source')
plt.xlabel('source')
plt.ylabel('% of session')
plt.tight_layout()
plt.show()

plt.bar(device_mix['device_type'],device_mix['pct_of_sessions'],color='lightgreen')
plt.title('session mix by device')
plt.xlabel('device')
plt.ylabel('% of session')
plt.tight_layout()
plt.show()

top_traffic_source=source_mix.iloc[0]
top_traffic_device=device_mix.iloc[0]
print(f"Insight: {top_traffic_source['utm_source']} sends the most traffic "
      f"({top_traffic_source['pct_of_sessions']}% of all sessions).")
print(f"Insight: {top_traffic_device['device_type']} sends the most traffic "
      f"({top_traffic_device['pct_of_sessions']}% of all sessions).")


# In[46]:


# which quarter carries the most revenue
orders['quarter']=orders['created_at'].dt.to_period('Q').astype(str)
revenue_by_quarter=orders.groupby('quarter')['price_usd'].sum().reset_index()
revenue_by_quarter=revenue_by_quarter.sort_values('quarter')

print('\n====== revenue by quater======')
print(revenue_by_quarter.to_string(index=False))

plt.figure(figsize=(7,4))
plt.bar(revenue_by_quarter['quarter'],revenue_by_quarter['price_usd'],color='red')
plt.title('revenue by quarter')
plt.xlabel('quarter')
plt.ylabel('price_usd')
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()

top_quarter=revenue_by_quarter.loc[revenue_by_quarter['price_usd'].idxmax()]
print(f"Insight: {top_quarter ['quarter']} is the strongest quarter ({top_quarter['price_usd']:.2f}).")


# In[47]:


# which month had the sharpest revenue swings  month-over-month?
monthly_revenue['pct_change']=monthly_revenue['price_usd'].pct_change().round(2)
swing_threshold=monthly_revenue['pct_change'].std()
biggest_jump=monthly_revenue.loc[monthly_revenue['pct_change'].idxmax()]
biggest_drop=monthly_revenue.loc[monthly_revenue['pct_change'].idxmin()]
print('\n======= month over month revenue  change (%) =========')
print(monthly_revenue[['months','price_usd','pct_change']].to_string(index=False))
print(f"insights: the sharpest jump was {biggest_jump['months']} ({biggest_jump['pct_change']:+.2f}%),"
      f"the sharpest drop was {biggest_drop['months']} ({biggest_drop['pct_change']:+.2f}%). "
      f"A swing bigger than {swing_threshold:.2f}% is outside the usual month-to-month range.")


# In[48]:


# distribution of order volume across days of the week — are certain days consistently higher or lower
orders['weekdays']=orders['created_at'].dt.day_name()
volume_distribution=orders.groupby('weekdays')['price_usd'].sum().reset_index(name='days_sales')
volume_distribution=volume_distribution.sort_values(by='days_sales',ascending=False)
volume_distribution
volume_distribution['days_contribution']=volume_distribution['days_sales']/sum(volume_distribution['days_sales'])*100
plt.figure(figsize=(7,3))
plt.pie(x=volume_distribution['days_contribution'],autopct='%1.1f')
plt.suptitle('days_contribution',fontweight='bold')
plt.show()


# ### Diagnostic analysis (why it happened)
# -- Diagnostic analysis asks questions about those numbers by comparing groups.

# In[49]:


merged_grp=sessions.merge(orders[['order_id','website_session_id']],on='website_session_id',how='left')


# In[50]:


# conversion by source  
conversion_by_source=merged_grp.groupby('utm_source').agg(sessions=('website_session_id','nunique'),orders=('order_id','nunique')).reset_index()
conversion_by_source['conversion_rate_pct']=(conversion_by_source['orders']/conversion_by_source['sessions']*100).round(2)
conversion_by_source=conversion_by_source.sort_values('conversion_rate_pct',ascending=False)
print('\n======conversion by source=======')
print(conversion_by_source.to_string(index=False))

plt.figure(figsize=(7,4))
plt.bar(conversion_by_source['utm_source'],conversion_by_source['conversion_rate_pct'],color='steelblue')
plt.title('conversion rate by source')
plt.xlabel('source')
plt.ylabel('conversion rate')
plt.tight_layout()
plt.show()

best_conv_source=conversion_by_source.iloc[0]
worst_conv_source=conversion_by_source.iloc[0]
print(f"Insight: {best_conv_source['utm_source']} converts best ({best_conv_source['conversion_rate_pct']}%), "
      f"{worst_conv_source['utm_source']} converts worst ({worst_conv_source['conversion_rate_pct']}%).")


# In[51]:


# conversion by device  
conversion_by_device=merged_grp.groupby('device_type').agg(sessions=('website_session_id','nunique'),orders=('order_id','nunique')).reset_index()
conversion_by_device['conversion_rate_pct']=(conversion_by_device['orders']/conversion_by_device['sessions']*100).round(2)
conversion_by_device=conversion_by_device.sort_values('conversion_rate_pct',ascending=False)
print('\n======conversion by source=======')
print(conversion_by_device.to_string(index=False))

plt.figure(figsize=(7,4))
plt.bar(conversion_by_device['device_type'],conversion_by_device['conversion_rate_pct'],color='steelblue')
plt.title('conversion_by_device')
plt.xlabel('device_type')
plt.ylabel('conversion rate')
plt.tight_layout()
plt.show()

best_conv_device=conversion_by_device.iloc[0]
worst_conv_device=conversion_by_device.iloc[0]
print(f"Insight: {best_conv_device['device_type']} converts best ({best_conv_device['conversion_rate_pct']}%), "
      f"{worst_conv_device['device_type']} converts worst ({worst_conv_device['conversion_rate_pct']}%).")


# In[52]:


# repeat vs new visitor conversion 
repeat_vs_new=merged_grp.groupby('is_repeat_session').agg(
    sessions=('website_session_id','nunique'),orders=('order_id','nunique'),
).reset_index()
repeat_vs_new['conversion_rate_pct']=(repeat_vs_new['orders']/repeat_vs_new['sessions']*100).round(2)
repeat_vs_new=repeat_vs_new.sort_values('conversion_rate_pct',ascending=False)
print('\n====== repeat vs new visitors========')
print(repeat_vs_new.to_string(index=False))

labels=['repeat' if v==1 else 'new' for v in repeat_vs_new['is_repeat_session']]
plt.figure(figsize=(5,4))
plt.bar(labels,repeat_vs_new['conversion_rate_pct'],color=['purple','grey'])
plt.title('repeat vs new visitor conversion')
plt.xlabel('visitor type')
plt.ylabel('conversion rate')
plt.tight_layout()
plt.show()

repeat_row=repeat_vs_new[repeat_vs_new['is_repeat_session']==1].iloc[0]
new_row=repeat_vs_new[repeat_vs_new['is_repeat_session']==0].iloc[0]
gap=repeat_row['conversion_rate_pct']-new_row['conversion_rate_pct']
print(f"Insight: Repeat visitors convert at {repeat_row['conversion_rate_pct']}% vs "
      f"{new_row['conversion_rate_pct']}% for new visitors — a {gap:.2f} point gap.")


# In[53]:


# refund rate by product 
items_with_product=order_items.merge(products,on='product_id')
items_with_refund=items_with_product.merge(
    refunds[['order_item_id','refund_amount_usd']],
    on='order_item_id',how='left'
)
items_with_refund['was_refunded']=items_with_refund['refund_amount_usd'].notna()
refund_rate_by_product=items_with_refund.groupby('product_name').agg(
    units_sold=('order_item_id','nunique'),
    units_refunded=('was_refunded','sum'),
    refund_amount=('refund_amount_usd','sum')
).reset_index()
refund_rate_by_product['refund_rate_pct']=(
    refund_rate_by_product['units_refunded']/refund_rate_by_product['units_sold']*100).round(2)
refund_rate_by_product=refund_rate_by_product.sort_values('refund_rate_pct',ascending=False)
print('\n======= refund rate by pproduct =======')
print(refund_rate_by_product.to_string(index=False))

plt.figure(figsize=(6,6))
plt.bar(refund_rate_by_product['product_name'],refund_rate_by_product['refund_rate_pct'],color='blue')
plt.title('refund rate by product')
plt.xlabel('product')
plt.ylabel('refund rate')
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()

worst_refund=refund_rate_by_product.iloc[0]
print(f"Insight: {worst_refund['product_name']} has the highest refund rate "
      f"({worst_refund['refund_rate_pct']}% of units sold).")


# In[54]:


# funnel drop off
total_session_f=sessions['website_session_id'].nunique()
sessions_with_pageview=website_pageviews['website_session_id'].nunique()
sessions_with_order=orders['website_session_id'].nunique()
funnel=pd.DataFrame({
    'stage':["landed(session started)","viewed page","placed an order"],
    'sessions':[total_session_f,sessions_with_pageview,sessions_with_order],
})
funnel['pct_of_landed']=(funnel['sessions']/total_session_f*100).round(2)
print('\n======funnel drop off========')
print(funnel.to_string(index=False))
plt.figure(figsize=(6,4))
plt.bar(funnel['stage'],funnel['sessions'],color='teal')
plt.title('funnel drop off')
plt.xlabel('stage')
plt.ylabel('sessions')
plt.tight_layout()
plt.show()

drop_pageview=100-funnel.loc[1,'pct_of_landed']
drop_order=funnel.loc[1,'pct_of_landed']-funnel.loc[2,'pct_of_landed']
biggest_drop_stage='landed->viewed a page' if drop_pageview>drop_order else "viewed a page->placed an order"
print(f"insights: the biggest drop-off happens between '{biggest_drop_stage}'.")


# In[55]:


## correlation check 
numeric_cols=['items_purchased','price_usd','cogs_usd']
correlation=orders[numeric_cols].corr().round(3)
print('\n===== correlation (orders level numeric fields)=======')
print(correlation.to_string())
plt.figure(figsize=(5,4))
plt.imshow(correlation,cmap='coolwarm',vmin=-1,vmax=1)
plt.colorbar(label='correlation')
plt.xticks(range(len(numeric_cols)),numeric_cols,rotation=45)
plt.yticks(range(len(numeric_cols)),numeric_cols)
for i in range(len(numeric_cols)):
    for j in range(len(numeric_cols)):
        plt.text(j,i,correlation.iloc[i,j],ha='center',va='center',color='black')
plt.title('correlation heatmap')
plt.tight_layout()
plt.show()



# ### predictive analysis -what's likely to happen

# In[56]:


from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score,precision_score,roc_auc_score,recall_score,f1_score,confusion_matrix,classification_report)
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer


# In[57]:


# Build session-level dataset: one row per session, label = converted ---
converted_ids=set(orders['website_session_id'].dropna())
sessions['converted']=sessions['website_session_id'].isin(converted_ids).astype(int)
categorical_features=['utm_source','utm_campaign','device_type']
binary_features=['is_repeat_session']
target='converted'
keep_cols=['website_session_id']+categorical_features+binary_features+[target]
dataset=sessions[keep_cols].dropna(subset=categorical_features+binary_features)

print('\n session dataset shape:',dataset.shape)
print('baseline conversion rate:{:.2f}%'.format(dataset[target].mean()*100))


# In[58]:


# ---  Feature engineering: one-hot encode categoricals, keep binary as-is ---
# OneHotEncoder (not LabelEncoder) because utm_source/device_type/utm_campaign
# have no natural order — LabelEncoder would wrongly imply one category is
# "greater than" another.

X=dataset[categorical_features+binary_features]
y=dataset[target]

preprocessor=ColumnTransformer(transformers=[
    ('cat',OneHotEncoder(handle_unknown='ignore'),categorical_features)],remainder='passthrough') # passes is_repeat_session through unchanged

#Train/test split (stratified — conversion is a minority class) ---
X_train,X_test,y_train,y_test=train_test_split(
    X,y,test_size=0.2,random_state=42,stratify=y)

# Fit logistic regression ---
# class_weight="balanced" matters — most sessions do NOT convert, and an
# unweighted model would just predict "no" for every session.

pipeline=Pipeline(steps=[
    ('preprocess',preprocessor),
    ('model',LogisticRegression(max_iter=1000,class_weight='balanced')),
])
pipeline.fit(X_train,y_train)

# Evaluate: accuracy, ROC-AUC, precision, recall, F1, confusion matrix ---
y_pred=pipeline.predict(X_test)
y_proba=pipeline.predict_proba(X_test)[:,1]

accuracy=accuracy_score(y_test,y_pred)
roc_auc=roc_auc_score(y_test,y_proba)
precision=precision_score(y_test,y_pred,zero_division=0)
recall=recall_score(y_test,y_pred,zero_division=0)
f1=f1_score(y_test,y_pred,zero_division=0)
cm=confusion_matrix(y_test,y_pred)

print('\n ====== model evaluation =====')
print('train rows:',len(X_train), "| test rows:",len(X_test))
print('Accuracy:',round(accuracy,4))
print('Precision:',round(precision,4))
print('Roc-auc-score:',round(roc_auc,4))
print('Recall:',round(recall,4))
print('F1:',round(f1,4))
print('"\nConfusion matrix [[TN, FP], [FN, TP]]:"):')
print(cm)
print('\n'+ classification_report(y_test,y_pred,zero_division=0))


# ### bulid streamlit

# In[60]:


import streamlit as st
import joblib
import os
import pickle


# In[61]:


##Save the fitted model so it can be reused in the web app ---
with open("conversion_model.pkl", "wb") as f:
    pickle.dump(pipeline, f)

print("Model saved to conversion_model.pkl")
print("\nPipeline complete.")


# In[63]:


with open("conversion_model.pkl", "rb") as f:
    model = pickle.load(f)


# In[ ]:




