"""Quick script to verify data types in Postgres database."""
import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / '.env')

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD')
)

cur = conn.cursor()

print("=" * 80)
print("DATA TYPE VERIFICATION FOR robot_vacuum_orders TABLE")
print("=" * 80)

# Check column data types from information_schema
print("\n1. Column Data Types (from information_schema):")
print("-" * 80)
cur.execute("""
    SELECT column_name, data_type, numeric_precision, numeric_scale 
    FROM information_schema.columns 
    WHERE table_name = 'robot_vacuum_orders' 
    AND column_name IN ('ShippingCost', 'TotalAmount', 'Quantity', 'ProductPrice', 'TaxAmount', 'DiscountAmount')
    ORDER BY column_name
""")

print(f"{'Column Name':<20} | {'Data Type':<20} | {'Precision':<10} | {'Scale':<10}")
print("-" * 80)
for row in cur.fetchall():
    precision = str(row[2]) if row[2] else "N/A"
    scale = str(row[3]) if row[3] else "N/A"
    print(f"{row[0]:<20} | {row[1]:<20} | {precision:<10} | {scale:<10}")

# Check using pg_typeof
print("\n2. Postgres Type Verification (using pg_typeof):")
print("-" * 80)
cur.execute("""
    SELECT 
        pg_typeof("ShippingCost") as shipping_type,
        pg_typeof("TotalAmount") as total_type,
        pg_typeof("Quantity") as qty_type,
        pg_typeof("ProductPrice") as price_type
    FROM robot_vacuum_orders 
    LIMIT 1
""")
type_row = cur.fetchone()
print(f"ShippingCost type: {type_row[0]}")
print(f"TotalAmount type:  {type_row[1]}")
print(f"Quantity type:     {type_row[2]}")
print(f"ProductPrice type: {type_row[3]}")

# Sample data
print("\n3. Sample Data (first 5 rows with numeric values):")
print("-" * 80)
cur.execute("""
    SELECT "ShippingCost", "TotalAmount", "Quantity", "ProductPrice"
    FROM robot_vacuum_orders 
    WHERE "ShippingCost" IS NOT NULL 
    LIMIT 5
""")
print(f"{'ShippingCost':<15} | {'TotalAmount':<15} | {'Quantity':<10} | {'ProductPrice':<15}")
print("-" * 80)
for row in cur.fetchall():
    print(f"{str(row[0]):<15} | {str(row[1]):<15} | {str(row[2]):<10} | {str(row[3]):<15}")

# Math operations test
print("\n4. Math Operations Test (proves numeric types, not strings):")
print("-" * 80)
cur.execute("""
    SELECT 
        SUM("ShippingCost") as total_shipping,
        AVG("TotalAmount") as avg_total,
        SUM("Quantity") as total_quantity,
        MAX("ProductPrice") as max_price
    FROM robot_vacuum_orders 
    WHERE "ShippingCost" IS NOT NULL
""")
result = cur.fetchone()
print(f"SUM(ShippingCost):  {result[0]}")
print(f"AVG(TotalAmount):   {result[1]:.2f}")
print(f"SUM(Quantity):     {result[2]}")
print(f"MAX(ProductPrice): {result[3]}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print("\nIf math operations succeeded, columns are NUMERIC types (not strings).")
print("This confirms the LLM can perform SUM, AVG, and other numeric operations.")

cur.close()
conn.close()

