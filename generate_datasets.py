import pandas as pd
import random
from datetime import datetime, timedelta

# =====================================================
# CONFIG
# =====================================================

NUM_ROWS = 250

# =====================================================
# MASTER DATA
# =====================================================

cities = [
"Pune","Mumbai","Nagpur","Nashik","Aurangabad","Kolhapur",
"Solapur","Amravati","Nanded","Akola","Jalgaon","Sangli",
"Satara","Latur","Dhule","Chandrapur","Parbhani","Yavatmal",
"Gondia","Bhandara","Ratnagiri","Sindhudurg","Beed","Osmanabad","Wardha"
]

materials = [
"Automotive Parts","Pharmaceuticals","Textiles","Plastic Granules",
"Steel Coils","Electronics","Consumer Goods","Machinery",
"Food Products","Construction Material","Chemical Drums"
]

carriers = [
"ABC_Logistics","FastCargo","BlueLine Transport",
"PrimeRoute Carriers","UrbanMove Logistics",
"ExpressHaul Pvt Ltd","MetroCargo Logistics",
"RapidHaul Logistics"
]

drivers = [
"Ramesh","Suresh","Mahesh","Rajesh","Amit","Deepak","Vijay","Arun",
"Manoj","Kiran","Ganesh","Santosh","Prakash","Anil","Sunil","Dinesh",
"Ravi","Ashok","Naresh","Mukesh","Ajay","Sanjay","Vinod","Mahendra",
"Rakesh","Nitin","Rahul","Sandeep","Pravin","Sachin","Shankar","Balaji",
"Kailash","Harish","Bharat","Gopal","Ravindra","Anand","Sudhir","Vikas",
"Tejas","Sameer","Yogesh","Hemant","Amol","Swapnil","Shailesh","Pankaj",
"Nilesh","Umesh","Rohit","Abhishek","Kunal","Chandan","Varun","Arvind",
"Kartik","Siddharth","Devendra","Tushar"
]

vehicle_letters = ["A","B","C","D","E","F","G","H"]

# =====================================================
# HELPERS
# =====================================================

def generate_vehicle():
    return f"MH12{random.choice(vehicle_letters)}{random.choice(vehicle_letters)}{random.randint(1000,9999)}"

# =====================================================
# DATA STORAGE
# =====================================================

lr_rows = []
pod_rows = []
invoice_rows = []

base_date = datetime(2024,1,1)

# =====================================================
# GENERATE DATA
# =====================================================

for i in range(NUM_ROWS):

    shipment_id = f"S{1000+i}"

    origin = random.choice(cities)
    destination = random.choice([c for c in cities if c != origin])

    carrier = random.choice(carriers)
    driver = random.choice(drivers)
    vehicle = generate_vehicle()

    dispatch_date = base_date + timedelta(days=random.randint(0,60))
    delivery_date = dispatch_date + timedelta(days=random.randint(1,4))

    package_count = random.randint(10,120)
    weight = round(random.uniform(1000,5000),2)
    charged_weight = weight + random.randint(0,200)

    freight = random.randint(5000,20000)
    loading = random.randint(200,800)
    unloading = random.randint(200,800)

    total_lr_amount = freight + loading + unloading

    material = random.choice(materials)

    anomaly = random.random() < 0.35

    received_packages = package_count
    invoice_total = total_lr_amount
    pod_status = "Delivered"

    if anomaly:

        anomaly_type = random.choice([
            "weight_mismatch",
            "package_mismatch",
            "invoice_mismatch",
            "delivery_delay",
            "missing_pod"
        ])

        if anomaly_type == "weight_mismatch":
            charged_weight += random.randint(200,800)

        elif anomaly_type == "package_mismatch":
            received_packages = package_count - random.randint(1,10)

        elif anomaly_type == "invoice_mismatch":
            invoice_total += random.randint(500,2000)

        elif anomaly_type == "delivery_delay":
            delivery_date += timedelta(days=random.randint(3,7))

        elif anomaly_type == "missing_pod":
            pod_status = "Pending"

    # LR DATA
    lr_rows.append({

        "Shipment_ID": shipment_id,
        "LR_Number": f"LR-{random.randint(10000,99999)}",
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
        "Total_LR_Amount": total_lr_amount

    })

    # POD DATA
    pod_rows.append({

        "Shipment_ID": shipment_id,
        "Delivery_ID": f"DEL-{random.randint(100000,999999)}",
        "Delivery_Date": delivery_date,
        "Status": pod_status,
        "Received_Packages": received_packages,
        "Receiver_Name": f"Receiver_{random.randint(1,80)}",
        "Latitude": round(random.uniform(18.5,19.5),6),
        "Longitude": round(random.uniform(72.5,73.5),6),
        "Signature_Available": random.choice(["Yes","No"])

    })

    # INVOICE DATA
    fuel_surcharge = random.randint(200,800)
    tax = round(invoice_total * 0.05,2)

    invoice_rows.append({

        "Shipment_ID": shipment_id,
        "Invoice_ID": f"INV-{random.randint(100000,999999)}",
        "Invoice_Date": delivery_date,
        "Carrier_Name": carrier,
        "Freight_Charge": freight,
        "Fuel_Surcharge": fuel_surcharge,
        "Subtotal": invoice_total,
        "Tax": tax,
        "Total_Invoice_Amount": invoice_total + tax

    })

# =====================================================
# CREATE DATAFRAMES
# =====================================================

lr_df = pd.DataFrame(lr_rows)
pod_df = pd.DataFrame(pod_rows)
invoice_df = pd.DataFrame(invoice_rows)

# =====================================================
# SAVE DATASETS
# =====================================================

lr_df.to_csv("lr_dataset.csv", index=False)
pod_df.to_csv("pod_dataset.csv", index=False)
invoice_df.to_csv("invoice_dataset.csv", index=False)

# =====================================================
# OUTPUT SUMMARY
# =====================================================

print("Datasets generated successfully")
print("LR:", lr_df.shape)
print("POD:", pod_df.shape)
print("Invoice:", invoice_df.shape)