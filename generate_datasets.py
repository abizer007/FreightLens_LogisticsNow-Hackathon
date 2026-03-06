"""
Generate realistic LR, POD, and Invoice datasets for LogisticsNow demos.
Schema and column names are fixed; only value generation is configurable.

Usage:
  python generate_datasets.py                    # 250 rows, current dir
  python generate_datasets.py --rows 500         # 500 rows
  python generate_datasets.py --output ./data    # save to ./data/
  python generate_datasets.py --rows 100 --output ./samples
"""

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# =====================================================
# CONFIG
# =====================================================

NUM_ROWS_DEFAULT = 250
ANOMALY_RATE = 0.25  # 20-30% of shipments have some anomaly

# =====================================================
# MASTER DATA (same as before)
# =====================================================

cities = [
    "Pune", "Mumbai", "Nagpur", "Nashik", "Aurangabad", "Kolhapur",
    "Solapur", "Amravati", "Nanded", "Akola", "Jalgaon", "Sangli",
    "Satara", "Latur", "Dhule", "Chandrapur", "Parbhani", "Yavatmal",
    "Gondia", "Bhandara", "Ratnagiri", "Sindhudurg", "Beed", "Osmanabad", "Wardha",
]

# Popular routes (origin, destination) – weighted for higher frequency
POPULAR_ROUTES = [
    ("Mumbai", "Pune"),
    ("Pune", "Mumbai"),
    ("Mumbai", "Nashik"),
    ("Nashik", "Mumbai"),
    ("Pune", "Nashik"),
    ("Nagpur", "Pune"),
    ("Mumbai", "Aurangabad"),
    ("Pune", "Kolhapur"),
]
# All other valid (origin, dest) pairs for variety
def _all_routes():
    return [(o, d) for o in cities for d in cities if o != d]

materials = [
    "Automotive Parts", "Pharmaceuticals", "Textiles", "Plastic Granules",
    "Steel Coils", "Electronics", "Consumer Goods", "Machinery",
    "Food Products", "Construction Material", "Chemical Drums",
]

# Carriers with weights: first 3 appear more often
carriers = [
    "ABC_Logistics", "FastCargo", "BlueLine Transport",
    "PrimeRoute Carriers", "UrbanMove Logistics",
    "ExpressHaul Pvt Ltd", "MetroCargo Logistics",
    "RapidHaul Logistics",
]
CARRIER_WEIGHTS = [3, 3, 2, 1, 1, 1, 1, 1]  # first 3 more frequent

drivers = [
    "Ramesh", "Suresh", "Mahesh", "Rajesh", "Amit", "Deepak", "Vijay", "Arun",
    "Manoj", "Kiran", "Ganesh", "Santosh", "Prakash", "Anil", "Sunil", "Dinesh",
    "Ravi", "Ashok", "Naresh", "Mukesh", "Ajay", "Sanjay", "Vinod", "Mahendra",
    "Rakesh", "Nitin", "Rahul", "Sandeep", "Pravin", "Sachin", "Shankar", "Balaji",
]
# First 12 drivers appear more often (operational pattern)
DRIVER_WEIGHTS = [2] * 12 + [1] * (len(drivers) - 12)

vehicle_letters = ["A", "B", "C", "D", "E", "F", "G", "H"]

# Maharashtra city approximate coordinates (Lat, Lon) for geographic realism
CITY_COORDS = {
    "Pune": (18.5204, 73.8567),
    "Mumbai": (19.0760, 72.8777),
    "Nagpur": (21.1458, 79.0882),
    "Nashik": (19.9975, 73.7898),
    "Aurangabad": (19.8762, 75.3433),
    "Kolhapur": (16.7050, 74.2433),
    "Solapur": (17.6599, 75.9064),
    "Amravati": (20.9374, 77.7796),
    "Nanded": (19.1530, 77.3050),
    "Akola": (20.7096, 77.0025),
    "Jalgaon": (21.0486, 75.5337),
    "Sangli": (16.8697, 74.5637),
    "Satara": (17.6919, 74.0009),
    "Latur": (18.4088, 76.5604),
    "Dhule": (20.9010, 74.7774),
    "Chandrapur": (19.9608, 79.2951),
    "Parbhani": (19.2612, 76.7794),
    "Yavatmal": (20.3888, 78.1204),
    "Gondia": (21.4602, 80.1920),
    "Bhandara": (21.1689, 79.6501),
    "Ratnagiri": (16.9944, 73.3000),
    "Sindhudurg": (16.0000, 73.5000),
    "Beed": (18.9894, 75.7563),
    "Osmanabad": (18.1667, 76.0500),
    "Wardha": (20.7453, 78.6022),
}


def _random_coord_for_city(city: str, spread: float = 0.05) -> tuple:
    """Return (lat, lon) near the city with small random spread."""
    base = CITY_COORDS.get(city, (19.0, 73.0))
    lat = round(base[0] + random.uniform(-spread, spread), 6)
    lon = round(base[1] + random.uniform(-spread, spread), 6)
    return (lat, lon)


def generate_vehicle():
    return f"MH12{random.choice(vehicle_letters)}{random.choice(vehicle_letters)}{random.randint(1000, 9999)}"


def choose_route() -> tuple:
    """Pick origin and destination; popular routes 50%, rest 50%."""
    all_r = _all_routes()
    if random.random() < 0.5 and POPULAR_ROUTES:
        return random.choice(POPULAR_ROUTES)
    return random.choice(all_r)


def main():
    parser = argparse.ArgumentParser(
        description="Generate LR, POD, and Invoice CSVs for LogisticsNow demos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=NUM_ROWS_DEFAULT,
        help=f"Number of shipments (default: {NUM_ROWS_DEFAULT})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="Directory to write CSV files (default: current directory)",
    )
    args = parser.parse_args()
    num_rows = max(1, args.rows)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    lr_rows = []
    pod_rows = []
    invoice_rows = []
    base_date = datetime(2024, 1, 1)

    for i in range(num_rows):
        shipment_id = f"S{1000 + i}"
        origin, destination = choose_route()
        carrier = random.choices(carriers, weights=CARRIER_WEIGHTS, k=1)[0]
        driver = random.choices(drivers, weights=DRIVER_WEIGHTS, k=1)[0]
        vehicle = generate_vehicle()
        material = random.choice(materials)

        # Dispatch across multiple weeks (e.g. 0–70 days from base)
        dispatch_date = base_date + timedelta(days=random.randint(0, 70))

        # Weight 800–5000 kg; package count correlates (roughly 15–40 kg per package band)
        weight = round(random.uniform(800, 5000), 2)
        avg_kg_per_pkg = random.uniform(18, 42)
        package_count = max(10, min(120, int(weight / avg_kg_per_pkg) + random.randint(-5, 10)))
        package_count = max(10, min(120, package_count))

        # Charged_Weight usually slightly higher (volumetric/rounding)
        charged_weight = round(weight + random.uniform(0, min(150, weight * 0.08)), 2)
        charged_weight = max(weight, charged_weight)

        # Freight depends on weight (heavier = higher freight)
        rate_per_kg = random.uniform(4, 7)
        freight = int(weight * rate_per_kg) + random.randint(-200, 500)
        freight = max(3000, min(45000, freight))
        loading = random.randint(200, 800)
        unloading = random.randint(200, 800)
        total_lr_amount = freight + loading + unloading

        # Delivery: most 1–3 days, some 3–6 days delay
        if random.random() < 0.75:
            delivery_days = random.randint(1, 3)
        else:
            delivery_days = random.randint(3, 6)
        delivery_date = dispatch_date + timedelta(days=delivery_days)

        received_packages = package_count
        pod_status = "Delivered"
        signature_available = "Yes"
        invoice_subtotal = total_lr_amount
        freight_charge = freight

        # Anomalies in 20–30% of shipments
        anomaly = random.random() < ANOMALY_RATE
        if anomaly:
            anomaly_type = random.choice([
                "weight_mismatch",
                "package_mismatch",
                "invoice_mismatch",
                "delivery_delay",
                "missing_pod",
                "missing_signature",
            ])
            if anomaly_type == "weight_mismatch":
                charged_weight = round(weight + random.uniform(200, 600), 2)
            elif anomaly_type == "package_mismatch":
                loss = random.randint(1, 3)
                received_packages = max(0, package_count - loss)
            elif anomaly_type == "invoice_mismatch":
                invoice_subtotal = total_lr_amount + random.randint(400, 2500)
            elif anomaly_type == "delivery_delay":
                delivery_date = dispatch_date + timedelta(days=random.randint(4, 7))
            elif anomaly_type == "missing_pod":
                pod_status = "Pending"
            elif anomaly_type == "missing_signature":
                signature_available = "No"

        # Data consistency: Received_Packages never negative
        received_packages = max(0, received_packages)

        # Invoice: Freight_Charge matches LR Freight for normal; use freight_charge we computed
        fuel_pct = random.uniform(0.08, 0.15)
        fuel_surcharge = int(freight_charge * fuel_pct)
        subtotal = invoice_subtotal
        tax_rate = 0.05
        tax = round(subtotal * tax_rate, 2)
        total_invoice_amount = round(subtotal + tax, 2)
        total_invoice_amount = max(1.0, total_invoice_amount)

        # GPS for destination city (POD delivery location)
        lat, lon = _random_coord_for_city(destination)

        lr_rows.append({
            "Shipment_ID": shipment_id,
            "LR_Number": f"LR-{random.randint(10000, 99999)}",
            "Transport_Company": carrier,
            "Vehicle_Number": vehicle,
            "Driver_Name": driver,
            "Origin": origin,
            "Destination": destination,
            "Dispatch_Date": dispatch_date,
            "Material": material,
            "Package_Count": package_count,
            "Weight_KG": weight,
            "Charged_Weight": charged_weight,
            "Freight": freight,
            "Loading_Charges": loading,
            "Unloading_Charges": unloading,
            "Total_LR_Amount": total_lr_amount,
        })

        pod_rows.append({
            "Shipment_ID": shipment_id,
            "Delivery_ID": f"DEL-{random.randint(100000, 999999)}",
            "Delivery_Date": delivery_date,
            "Status": pod_status,
            "Received_Packages": received_packages,
            "Receiver_Name": f"Receiver_{random.randint(1, 80)}",
            "Latitude": lat,
            "Longitude": lon,
            "Signature_Available": signature_available,
        })

        invoice_rows.append({
            "Shipment_ID": shipment_id,
            "Invoice_ID": f"INV-{random.randint(100000, 999999)}",
            "Invoice_Date": delivery_date,
            "Carrier_Name": carrier,
            "Freight_Charge": freight_charge,
            "Fuel_Surcharge": fuel_surcharge,
            "Subtotal": subtotal,
            "Tax": tax,
            "Total_Invoice_Amount": total_invoice_amount,
        })

    lr_df = pd.DataFrame(lr_rows)
    pod_df = pd.DataFrame(pod_rows)
    invoice_df = pd.DataFrame(invoice_rows)

    lr_path = out_dir / "lr_dataset.csv"
    pod_path = out_dir / "pod_dataset.csv"
    inv_path = out_dir / "invoice_dataset.csv"
    lr_df.to_csv(lr_path, index=False)
    pod_df.to_csv(pod_path, index=False)
    invoice_df.to_csv(inv_path, index=False)

    print("Datasets generated successfully")
    print(f"  Rows: {num_rows}")
    print(f"  LR:       {lr_path}")
    print(f"  POD:      {pod_path}")
    print(f"  Invoice:  {inv_path}")
    print(f"  Shapes:  LR {lr_df.shape}, POD {pod_df.shape}, Invoice {invoice_df.shape}")


if __name__ == "__main__":
    main()
