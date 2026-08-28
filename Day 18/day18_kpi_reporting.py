# DAY 18 - KPI REPORTING
# ------------------------------------------------------------
# BUSINESS KPI REPORTING USING CAPSTONE DATASET
# ------------------------------------------------------------

import os
from pathlib import Path
import pandas as pd

# ------------------------------------------------------------
# 1: LOAD DATA
# ------------------------------------------------------------

# Read files from the same folder as this Python script.
BASE_DIR = Path(__file__).resolve().parent

customer_options = [
    BASE_DIR / "Capstone Customers.csv",
]
order_options = [
    BASE_DIR / "Capstone Orders.csv",
]

CUSTOMERS_FILE = next((p for p in customer_options if p.exists()), None)
ORDERS_FILE = next((p for p in order_options if p.exists()), None)

if CUSTOMERS_FILE is None or ORDERS_FILE is None:
    raise FileNotFoundError(
        "Please keep the Capstone Customers.csv and Capstone Orders.csv "
        "files in the same folder as this script."
    )

customers = pd.read_csv(CUSTOMERS_FILE)
orders = pd.read_csv(ORDERS_FILE)

print("DAY 18 - KPI REPORTING")
print("=" * 65)
print(f"Customers loaded : {customers.shape}")
print(f"Orders loaded    : {orders.shape}")


# ------------------------------------------------------------
# 2: DATA CLEANING
# ------------------------------------------------------------

# Convert dates to proper datetime format.
customers["JoinDate"] = pd.to_datetime(customers["JoinDate"], errors="coerce")
orders["OrderDate"] = pd.to_datetime(orders["OrderDate"], errors="coerce")

# Standardize text values.
customers["Region"] = (
    customers["Region"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
    .str.title()
)

customers["Segment"] = (
    customers["Segment"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
    .str.title()
)

orders["Category"] = (
    orders["Category"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
    .str.title()
)

# Remove invalid quantities because Quantity <= 0 is not a valid sale.
orders = orders[orders["Quantity"] > 0].copy()

# Remove exact duplicate order records.
orders = orders.drop_duplicates()

# Remove orders whose CustomerID does not exist in Customers.
orders = orders[orders["CustomerID"].isin(customers["CustomerID"])].copy()

# Sales is required for revenue KPIs. Since missing Sales cannot be
# reliably reconstructed from the available columns, those rows are removed.
orders = orders.dropna(subset=["Sales"]).copy()

# Remove duplicate CustomerID master records before merging.
# This prevents one order from being counted more than once.
customers = customers.drop_duplicates(subset=["CustomerID"], keep="first").copy()

# Merge customer information with cleaned orders.
data = orders.merge(
    customers[
        ["CustomerID", "CustomerName", "Region", "Segment", "JoinDate"]
    ],
    on="CustomerID",
    how="inner"
)

print("\nCLEANING SUMMARY")
print("-" * 65)
print(f"Customers after cleaning : {len(customers)}")
print(f"Orders after cleaning    : {len(orders)}")
print(f"Merged analysis rows     : {len(data)}")


# ------------------------------------------------------------
# 3: KPI CALCULATIONS
# ------------------------------------------------------------

# KPI 1: TOTAL REVENUE
# Who looks at it: CEO / Finance Manager / Sales Manager.
# Decision: Measures the overall sales value and helps management
# set revenue targets, budgets and growth plans.
total_revenue = data["Sales"].sum()

# KPI 2: AVERAGE ORDER VALUE (AOV)
# Who looks at it: Sales Manager / Marketing Manager / E-commerce Manager.
# Decision: Shows the average value of an order and helps decide
# upselling, cross-selling and bundle strategies.
number_of_orders = data["OrderID"].nunique()
average_order_value = total_revenue / number_of_orders

# KPI 3: NUMBER OF REPEAT CUSTOMERS
# Who looks at it: CRM / Marketing / Customer Success teams.
# Decision: Shows how many customers purchased more than once and
# helps evaluate loyalty campaigns and repeat-purchase programs.
orders_per_customer = data.groupby("CustomerID")["OrderID"].nunique()
repeat_customers = (orders_per_customer > 1).sum()

# KPI 4: CUSTOMER RETENTION RATE
# Required definition for this assignment:
# customers with more than one order / total customers * 100.
# Who looks at it: CRM Manager / Marketing Manager / Customer Success.
# Decision: Helps determine whether the business is keeping customers
# and whether retention programs need improvement.
total_customers = customers["CustomerID"].nunique()
retention_rate = (repeat_customers / total_customers) * 100

# KPI 5: REVENUE PER REGION
# Who looks at it: Regional Sales Managers / Sales Director.
# Decision: Identifies strong and weak regions for sales investment,
# targets, staffing and regional marketing.
revenue_per_region = (
    data.groupby("Region")["Sales"]
    .sum()
    .sort_values(ascending=False)
)

# KPI 6: REVENUE PER CATEGORY
# Who looks at it: Product Manager / Category Manager / Sales Manager.
# Decision: Identifies high-performing and weak product categories
# for inventory, promotion and product strategy.
revenue_per_category = (
    data.groupby("Category")["Sales"]
    .sum()
    .sort_values(ascending=False)
)


# ------------------------------------------------------------
# 4: PRINT THE 6 KPIs
# ------------------------------------------------------------

print("\n6 KEY PERFORMANCE INDICATORS")
print("=" * 65)

print(f"1. Total Revenue             : ₹{total_revenue:,.2f}")
print(f"2. Average Order Value       : ₹{average_order_value:,.2f}")
print(f"3. Repeat Customers          : {repeat_customers}")
print(f"4. Customer Retention Rate   : {retention_rate:.2f}%")

print("\n5. Revenue per Region")
print("-" * 65)
for region, revenue in revenue_per_region.items():
    print(f"{region:<15} : ₹{revenue:,.2f}")

print("\n6. Revenue per Category")
print("-" * 65)
for category, revenue in revenue_per_category.items():
    print(f"{category:<15} : ₹{revenue:,.2f}")


# ------------------------------------------------------------
# 5: COHORT ANALYSIS
# ------------------------------------------------------------

# Customers are grouped by the month in which they joined.
# Then we calculate total Sales generated by each customer cohort.
data["CohortMonth"] = data["JoinDate"].dt.to_period("M").astype(str)

cohort_sales = (
    data.groupby("CohortMonth")["Sales"]
    .sum()
    .sort_index()
)

print("\nCOHORT VIEW - TOTAL SALES BY JOIN MONTH")
print("=" * 65)
for cohort, sales in cohort_sales.items():
    print(f"{cohort} : ₹{sales:,.2f}")


# ------------------------------------------------------------
# 6: BEST AND WORST KPI
# ------------------------------------------------------------

# BEST KPI:
# Customer Retention Rate = 100.00%.
# Why: Every cleaned customer has more than one order, so the dataset
# indicates extremely strong repeat purchasing. This suggests that
# existing customers are highly engaged and the business can focus
# on protecting this loyalty while growing new customers.
#
# WORST KPI:
# Revenue per Category - Books = ₹2,511.96.
# Why: Books generate the lowest category revenue in this dataset,
# far below Electronics. Management should investigate demand,
# pricing, promotion and product assortment before increasing
# investment in this category.


# ------------------------------------------------------------
# 7: INTERPRETATION QUESTIONS
# ------------------------------------------------------------

# Q1. Pick one KPI and explain how it could be reported misleadingly.
#
# KPI: Customer Retention Rate.
# Misleading but technically true version:
# "Our customer retention rate is 100%, so our customer base is perfect."
#
# Honest version:
# "The retention rate is 100% under this assignment's definition because
# all 70 cleaned customers placed more than one order. However, this
# definition is unusual compared with many business retention definitions,
# which often use a time period and a starting customer cohort. Therefore,
# this 100% should not automatically be interpreted as long-term retention."

# Q2. Difference between bad news and noise:
#
# A KPI going down is bad news when the decline is large, persistent,
# and supported by other related metrics. It may be noise when the change
# is small, temporary, or caused by a small sample / random variation.
#
# With this data, compare the KPI across months, regions and categories.
# A repeated decline across several periods or multiple regions is more
# concerning than a one-period change. We should also check order counts
# and customer counts before concluding that the KPI truly deteriorated.


# ------------------------------------------------------------
# 8: END-OF-DAY CHECK - ONE SENTENCE EACH
# ------------------------------------------------------------

# Vanity metric:
# A vanity metric looks impressive but does not clearly help a business
# make a decision or measure meaningful progress.

# Why retention matters more than total customer count:
# Total customer count can increase even if existing customers leave,
# while retention shows whether the business is keeping its customers.

# What to ask before trusting a KPI:
# Ask how the KPI is defined, what time period and population it covers,
# whether the data is complete, and whether the number is comparable
# with a baseline or target.

print("\nBEST KPI")
print("-" * 65)
print(f"Customer Retention Rate : {retention_rate:.2f}%")

print("\nWORST KPI")
print("-" * 65)
print(
    f"Lowest Category Revenue - Books : "
    f"₹{revenue_per_category.get('Books', 0):,.2f}"
)

print("\nREPORT COMPLETE")
