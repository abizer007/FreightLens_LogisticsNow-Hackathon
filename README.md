# LogisticsNow Exception Intelligence Console

**AI-Powered LR–POD–Invoice Reconciliation System**

*Building the Digital Backbone of Logistics*

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Data Generation](#data-generation)
- [Data Schema](#data-schema)
- [Pipeline & Modules](#pipeline--modules)
- [UI & Navigation](#ui--navigation)
- [Brand & Theming](#brand--theming)
- [Configuration](#configuration)
- [License](#license)

---

## Overview

The **LogisticsNow Exception Intelligence Console** is a production-style prototype for logistics document analysis. It ingests **LR (Lorry Receipt)**, **POD (Proof of Delivery)**, and **Invoice** datasets, merges them, detects discrepancies, computes risk scores, runs fraud checks, and surfaces operational and financial insights through a Streamlit dashboard.

**Key capabilities:**

- **LR, POD, and Invoice ingestion** via CSV upload
- **Data validation and cleaning** (realistic bounds, outlier handling)
- **Reconciliation** (merge on Shipment ID, discrepancy detection)
- **Weighted risk scoring** (quantity, invoice, delay, weight, missing POD/signature)
- **Four-level risk classification** (Low, Medium, High, Critical)
- **Fraud detection** (duplicate invoices, repeated driver/carrier anomalies, cost inflation, repeated missing PODs)
- **Operational analytics** (carrier/driver/lane risk, delay trends, POD compliance)
- **Executive dashboard** and **Control Tower** views (map, alerts, heatmaps, AI copilot)

The system is built for **LogisticsNow**-style use: professional, data-driven, and hackathon-ready.

---

## Architecture

### High-Level Data Flow

```mermaid
flowchart TB
    subgraph input [Input]
        LR[LR CSV]
        POD[POD CSV]
        INV[Invoice CSV]
    end
    subgraph backend [Backend Pipeline]
        Load[data_loader]
        Valid[validators]
        Clean[data_cleaning]
        Recon[reconciliation_engine]
        Risk[risk_engine]
        Fraud[fraud_detection]
        Insights[insights_engine]
    end
    subgraph ui [Streamlit UI]
        App[app.py]
        Reports[Reports: Dashboard, Shipment, Ops, Finance, Fraud]
        ControlTower[Logistics Control Tower: 7 views]
    end
    LR --> Load
    POD --> Load
    INV --> Load
    Load --> Valid
    Valid --> Clean
    Clean --> Recon
    Recon --> Risk
    Recon --> Fraud
    Risk --> Insights
    backend --> App
    App --> Reports
    App --> ControlTower
```

### Module Dependency Diagram

```mermaid
flowchart LR
    subgraph entry [Entry]
        App[app.py]
    end
    subgraph modules [modules/]
        Loader[data_loader]
        Valid[validators]
        Clean[data_cleaning]
        Recon[reconciliation_engine]
        Risk[risk_engine]
        FraudMod[fraud_detection]
        Insights[insights_engine]
    end
    subgraph ui [ui/]
        Dash[dashboard]
        Ship[shipment_analysis]
        Ops[operations]
        Fin[finance]
        FraudUI[fraud]
        ControlTower[control_tower_views]
        Brand[brand_css]
    end
    App --> Loader
    App --> Valid
    App --> Clean
    App --> Recon
    App --> Risk
    App --> FraudMod
    App --> Insights
    App --> Dash
    App --> Ship
    App --> Ops
    App --> Fin
    App --> FraudUI
    App --> ControlTower
    App --> Brand
    Recon --> Risk
    Risk --> Insights
    FraudMod --> FraudUI
    Insights --> Dash
    Insights --> Ops
    Insights --> Fin
```

### Pipeline Sequence (After Upload)

```mermaid
sequenceDiagram
    participant User
    participant App
    participant Loader
    participant Valid
    participant Clean
    participant Recon
    participant Risk
    participant Fraud
    participant Insights
    User->>App: Upload LR, POD, Invoice CSVs
    App->>Loader: (cached) load CSVs
    Loader->>App: lr_df, pod_df, inv_df
    App->>Recon: merge_documents(lr, pod, inv)
    Recon->>App: merged
    App->>Recon: detect_discrepancies(merged)
    Recon->>App: merged + discrepancy cols
    App->>Valid: validate_and_normalize_merged(merged)
    Valid->>App: merged + flags
    App->>Clean: clean_dataset(merged)
    Clean->>App: cleaned
    App->>Clean: strip_validation_columns(cleaned)
    App->>Risk: run_risk_pipeline(merged)
    Risk->>App: merged + Risk_Score, Risk_Level, Investigation
    App->>Fraud: run_fraud_detection(merged)
    Fraud->>App: fraud_flags DataFrame
    App->>Insights: carrier_risk, delay_trends, heatmap, etc.
    Insights->>App: context dict
    App->>User: Render sidebar + selected view
```

---

## Project Structure

```
.
├── app.py                    # Streamlit entry; upload, pipeline, navigation
├── generate_datasets.py      # CLI to generate LR, POD, Invoice CSVs
├── requirements.txt          # Python dependencies
├── run_app.bat               # Windows batch script to run app
├── run_app.ps1               # PowerShell script to run app
├── README.md                 # This file
├── .gitignore
│
├── modules/                  # Backend logic
│   ├── __init__.py
│   ├── data_loader.py        # Load LR, POD, Invoice CSVs
│   ├── data_cleaning.py      # clean_dataset(), strip_validation_columns()
│   ├── validators.py         # Validation rules; flag, normalize, log
│   ├── reconciliation_engine.py  # merge_documents(), detect_discrepancies()
│   ├── risk_engine.py        # Weighted risk score, 4 levels, recommendations, investigation
│   ├── fraud_detection.py    # Duplicate/repeated/suspicious detection
│   └── insights_engine.py   # Carrier/driver/lane risk, heatmap, delay, POD compliance
│
└── ui/                       # Streamlit UI
    ├── __init__.py
    ├── brand_css.py          # Brand CSS, tagline, sidebar styles, table styles
    ├── dashboard.py          # Executive Dashboard (metrics + charts)
    ├── shipment_analysis.py  # Shipment Risk Analysis (table, drill-down)
    ├── operations.py        # Operational Intelligence (carrier, driver, lane, delay, POD)
    ├── finance.py            # Financial Intelligence (exposure, heatmap, charges)
    ├── fraud.py              # Fraud & Compliance (flagged shipments)
    └── control_tower_views.py # Control Tower: 7 views (map, alerts, carrier, route, finance, fraud, copilot)
```

---

## Tech Stack

| Layer        | Technology |
|-------------|------------|
| Frontend    | Streamlit |
| Backend     | Python 3.x |
| Data        | pandas, numpy |
| Charts      | Plotly (plotly.express) |
| Fonts       | Google Fonts (Poppins, Source Sans Pro) |
| Logging     | Python `logging` |
| Caching     | `@st.cache_data` for pipeline |

---

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd AI-Document-Intelligence-LR-POD-Invoice-Matching-Agent_LogisticsNow-Hackathon
   ```

2. **Create a virtual environment (recommended)**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   Core dependencies: `streamlit`, `pandas`, `numpy`, `plotly`.

---

## Running the Application

**Option 1 – Command line**

```bash
streamlit run app.py --server.port 8501
```

Or with headless mode (no email prompt):

```bash
streamlit run app.py --server.port 8501 --server.headless true
```

**Option 2 – Scripts**

- **Windows (batch):** double-click `run_app.bat` or run `run_app.bat` from a terminal.
- **PowerShell:** `.\run_app.ps1`

**Open in browser:** `http://localhost:8501`

Then upload the three CSVs (LR, POD, Invoice) to run the pipeline and use the dashboard.

---

## Data Generation

Sample datasets can be generated with the same schema expected by the app.

**Basic usage (250 rows, current directory):**

```bash
python generate_datasets.py
```

**Options:**

| Option      | Description |
|------------|-------------|
| `--rows N` | Number of shipments (default: 250) |
| `--output DIR` | Output directory for CSVs (default: current directory) |

**Examples:**

```bash
python generate_datasets.py --rows 500
python generate_datasets.py --output ./data
python generate_datasets.py --rows 100 --output ./samples
```

**Output files:** `lr_dataset.csv`, `pod_dataset.csv`, `invoice_dataset.csv`

The generator produces realistic patterns: popular routes (e.g. Mumbai–Pune), weight-based freight, invoice logic (fuel surcharge, tax), anomalies (missing POD, delays, mismatches), and Maharashtra city coordinates for POD.

---

## Data Schema

### LR Dataset (`lr_dataset.csv`)

| Column             | Description |
|--------------------|-------------|
| Shipment_ID        | Unique shipment key |
| LR_Number          | Lorry receipt number |
| Transport_Company  | Carrier name |
| Vehicle_Number     | Vehicle ID |
| Driver_Name        | Driver name |
| Origin             | Origin city |
| Destination        | Destination city |
| Dispatch_Date      | Dispatch date |
| Material           | Material type |
| Package_Count      | Number of packages |
| Weight_KG          | Weight in kg |
| Charged_Weight     | Charged weight (e.g. volumetric) |
| Freight            | Freight amount |
| Loading_Charges    | Loading charges |
| Unloading_Charges  | Unloading charges |
| Total_LR_Amount   | Total LR amount |

### POD Dataset (`pod_dataset.csv`)

| Column             | Description |
|--------------------|-------------|
| Shipment_ID        | Links to LR/Invoice |
| Delivery_ID        | Delivery reference |
| Delivery_Date       | Delivery date |
| Status             | e.g. Delivered, Pending |
| Received_Packages  | Packages received |
| Receiver_Name      | Receiver name |
| Latitude           | Delivery latitude |
| Longitude          | Delivery longitude |
| Signature_Available| Yes/No |

### Invoice Dataset (`invoice_dataset.csv`)

| Column               | Description |
|----------------------|-------------|
| Shipment_ID          | Links to LR/POD |
| Invoice_ID           | Invoice reference |
| Invoice_Date         | Invoice date |
| Carrier_Name         | Carrier name |
| Freight_Charge       | Freight charge |
| Fuel_Surcharge       | Fuel surcharge |
| Subtotal             | Subtotal |
| Tax                  | Tax amount |
| Total_Invoice_Amount | Total invoice amount |

---

## Pipeline & Modules

### 1. `data_loader.py`

- **`load_lr_pod_invoice(lr_file, pod_file, invoice_file)`**  
  Returns `(lr_df, pod_df, inv_df)` from CSV file-like objects.

### 2. `validators.py`

- **`validate_and_normalize_merged(merged)`**  
  Applies: freight positive, invoice difference cap, delivery delay bounds, weight/package consistency. Adds validation flags and normalizes; logs warnings.

### 3. `data_cleaning.py`

- **`clean_dataset(df)`**  
  Outlier handling (IQR), null handling, numeric validation, realistic bounds.
- **`strip_validation_columns(df)`**  
  Drops internal `_*` columns before UI/analytics.

### 4. `reconciliation_engine.py`

- **`merge_documents(lr, pod, invoice)`**  
  Left joins on `Shipment_ID` (LR–POD–Invoice).
- **`detect_discrepancies(merged)`**  
  Adds: Quantity_Difference, Expected_Amount, Invoice_Difference, Weight_Difference, Delivery_Delay_Days, Missing_Signature, POD_Missing.

### 5. `risk_engine.py`

- **`compute_risk_score(merged)`**  
  Weighted formula: quantity×5 + invoice_scaled×3/1000 + delay×4 + weight×2/100 + missing_sig×20 + missing_pod×30. Adds Risk_Score, Risk_Level (Low/Medium/High/Critical).
- **`add_recommendations(merged)`**  
  Adds Recommended_Action per row.
- **`generate_investigation(row)`**  
  Returns structured dict: Shipment_ID, Detected_Issues, Operational_Impact, Financial_Risk, Suggested_Action.
- **`run_risk_pipeline(merged)`**  
  Runs score, level, recommendations, and investigations.

### 6. `fraud_detection.py`

- **`run_fraud_detection(merged)`**  
  Returns DataFrame of flagged shipments (Shipment_ID, Reason, Severity). Detects: duplicate invoices, repeated driver anomalies, repeated carrier mismatches, suspicious cost inflation, repeated missing PODs.

### 7. `insights_engine.py`

- **`carrier_risk_score(merged)`**, **`driver_risk_score(merged)`**, **`lane_risk_score(merged)`**
- **`financial_exposure_heatmap_data(merged)`**
- **`suspicious_carrier_detection(merged)`**, **`shipment_delay_trends(merged)`**
- **`pod_compliance_rate(merged)`**, **`auto_investigation_summary(merged)`**

---

## UI & Navigation

### Sidebar

- **LogisticsNow Intelligence Console** (title)
- **Reports** (heading)  
  - **View** dropdown: Executive Dashboard, Shipment Risk Analysis, Operational Intelligence, Financial Intelligence, Fraud & Compliance
- **Logistics Control Tower** (heading)  
  - Buttons: Control Tower, Shipment Intelligence, Carrier Analytics, Route Intelligence, Financial Risk, Fraud Detection, AI Logistics Copilot

### Reports Views

- **Executive Dashboard:** Top metrics (Total Shipments, High/Critical Risk, Financial Exposure, POD Compliance %); Risk distribution; Carrier risk ranking; Delay distribution; Financial risk breakdown; Auto investigation summary.
- **Shipment Risk Analysis:** Filter by risk level; risk table; shipment drill-down with structured AI investigation.
- **Operational Intelligence:** Carrier/Driver/Lane risk scores; delay trends; POD compliance %.
- **Financial Intelligence:** Financial exposure; freight cost composition; financial exposure heatmap.
- **Fraud & Compliance:** Flagged shipments table; duplicate invoices; missing POD/signature.

### Control Tower Views

- **Control Tower:** Hero metrics (shipments, risk counts, financial exposure, avg delay); brand values footer.
- **Shipment Intelligence:** Shipment map (Lat/Long, risk-colored); Logistics Alert Center (missing POD, delay, invoice/package mismatch).
- **Carrier Analytics:** Carrier leaderboard; Top risky carriers; Best performing carriers.
- **Route Intelligence:** Most delayed routes; Most risky routes; Highest volume routes.
- **Financial Risk:** Cost leakage (invoice/weight/package mismatch); Potential Recoverable Amount; heatmap table.
- **Fraud Detection:** Drivers with highest risk; Carriers with repeated mismatches; Routes with frequent delays.
- **AI Logistics Copilot:** Rule-based Q&A (e.g. carriers causing delays, risky routes, shipments needing investigation).

---

## Brand & Theming

- **Fonts:** Poppins (headings), Source Sans Pro (body) via Google Fonts.
- **Colors:** Primary green `#51aa3a`, white `#ffffff`, dark `#21242b`, light `#f2f4f8`.
- **Tagline:** “Building the Digital Backbone of Logistics.”
- **Values:** Trust, Neutrality, Efficiency, Visibility, Innovation (footer).
- **Sidebar:** Green section headings; dark buttons with green border/hover.
- **Tables:** Alternating row colors, bold dark header, row hover, responsive container (CSS in `brand_css.py`).

---

## Configuration

- **Logging:** Configured in `app.py` (level INFO, console).
- **Cache:** Pipeline cached with `@st.cache_data(ttl=3600)`; key from upload file bytes hash.
- **Risk thresholds:** In `risk_engine.py` (e.g. THRESHOLD_MEDIUM=25, THRESHOLD_HIGH=60, THRESHOLD_CRITICAL=120).
- **Validation bounds:** In `validators.py` (e.g. INVOICE_DIFF_CAP, DELAY_DAYS_MAX).

---

## License

See the LICENSE file in the repository.

---

*LogisticsNow Exception Intelligence Console – AI-Powered LR–POD–Invoice Reconciliation.*
