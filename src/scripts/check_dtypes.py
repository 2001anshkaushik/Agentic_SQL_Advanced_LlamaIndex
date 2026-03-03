"""Check DataFrame dtypes before insertion."""
import polars as pl
import pandas as pd
from pathlib import Path

csv_path = Path(__file__).parent.parent / 'data' / 'RobotVacuumDepot_MasterData_v125.csv'
df_polars = pl.read_csv(csv_path)
df = df_polars.to_pandas()

# Apply the same transformations as db_setup.py
date_columns = ['OrderDate', 'LastRestockDate', 'LastUpdated', 'ExpectedDeliveryDate', 'ActualDeliveryDate', 'ReviewDate']
for col in date_columns:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], format='%m/%d/%Y %H:%M', errors='coerce')

numeric_columns = ['ShippingCost', 'ProductPrice', 'TaxAmount', 'DiscountAmount', 'TotalAmount', 'UnitPrice', 'ReviewRating']
for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

integer_columns = ['CustomerZipCode', 'BillingZipCode', 'DeliveryZipCode', 'WarehouseZipCode', 'DistributionCenterZipCode', 'StockLevel', 'WarehouseCapacity', 'LeadTimeDays', 'ReliabilityScore', 'FleetSize', 'RestockThreshold', 'Quantity']
for col in integer_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

print("DataFrame dtypes for key columns:")
print(f"Quantity: {df['Quantity'].dtype}")
print(f"ShippingCost: {df['ShippingCost'].dtype}")
print(f"TotalAmount: {df['TotalAmount'].dtype}")
print(f"\nSample Quantity values:")
print(df['Quantity'].head(10))
print(f"\nQuantity has NaN: {df['Quantity'].isna().any()}")
print(f"Quantity NaN count: {df['Quantity'].isna().sum()}")

