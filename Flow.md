# Project Flow & File Guide

## Overview
This repository contains multiple interfaces (Tkinter, Streamlit, and Gradio) for tracking food and water intake, plus a medical-report extraction pipeline and optional Kafka publishing. The core flow is:

1. **User interface (UI) layer** collects intake data or PDF reports.
2. **Database layer (MySQL)** persists user/auth data, food/water logs, and reference food items.
3. **Analytics layer** aggregates macros and calories for visualization.
4. **Medical report extraction** parses PDFs into structured JSON (context + parameters).
5. **Kafka integration (optional)** publishes extracted report data to Kafka topics.

---

## Runtime Flows

### 1) Streamlit App Flow (primary Docker entrypoint)
**File:** `healthTrackerAppStreamlit.py`

- **Startup:** Loads environment variables, reads DB config from `.streamlit/secrets.toml`, sets API keys, and initializes tables if missing.
- **Database setup:** Creates `users`, `food_intake`, `food_items`, and `water_intake` tables, then populates `food_items` from `food_items.xlsx`.
- **Auth:** Login/register flow in sidebar. Auth state is stored in `st.session_state`.
- **Food intake:** Uses `food_items` to populate dropdowns, inserts rows into `food_intake`.
- **Water intake:** Inserts rows into `water_intake`.
- **Analytics:** Aggregates macros/calories with SQL and visualizes with Plotly.
- **Health report processing:** Uploads a PDF, extracts context + parameters, saves JSON output, and moves the PDF to a datastore.

### 2) Gradio App Flow (alternate UI)
**File:** `healthTrackerAppGradio.py`

- **Startup:** Reads DB configuration from environment variables and creates tables if missing.
- **Auth:** Simple login/register in Gradio tabs with a shared state object.
- **Food/water intake:** Inserts to `food_intake` and `water_intake` tables; supports delete-last-entry.
- **Analytics:** Provides “Last Month Data” and “Metrics” tabs and renders Plotly charts.
- **Health report processing:** Uploads a PDF, extracts context + parameters, writes JSON to `HealthReport/<user>/processed_report/<date>/`.

### 3) Tkinter Desktop App Flow (legacy/local)
**File:** `healthTrackerApp.py`

- **Startup:** Uses local MySQL settings, creates `health_data`, `food_items`, and `water_intake` tables.
- **Food tabs:** Separate tabs for breakfast/lunch/dinner entries.
- **Water tab:** Simple per-day water logging with delete-last-entry.
- **Food items:** Populates the list from `food_items.xlsx`.

---

## Medical Report Extraction Flow

### High-Level Pipeline
**File:** `medical_extractor_project/README.md`

- **PDF text loading**
- **Phase 1 (semantic detection):** Identify which parameters exist in the report.
- **Phase 2 (extraction):** Use regex first, fall back to LLM if needed.
- **Output:** Structured JSON of parameters.

### Orchestration
**File:** `medical_extractor_project/main.py`

- Loads PDF text.
- Detects report parameters using `phase1_semantic.parameter_detector`.
- Extracts values with regex (`phase2_extraction.regex_extractor`) and LLM fallback (`phase2_extraction.llm_extractor`).
- Returns a dictionary of extracted parameters.

### Context Extraction Agent
**File:** `Agents/HealthReport_InformationAgent.py`

- Uses LangChain loaders and Pydantic AI to extract `name`, `date`, `gender`, and `location` from PDF chunks.
- Used by both Streamlit and Gradio apps during health report processing.

### Parameter Extraction Agent (alternate/experimental)
**File:** `Agents/HealthReportParameterAgent.py`

- Uses Pydantic AI to extract parameter name/value/unit pairs from PDF chunks.
- Returns a dictionary keyed by parameter name.

---

## Kafka Integration Flow (optional)

### Plain JSON Producer
**File:** `Kafka/kafka_producer.py`

- Publishes extracted report data (dict) to the `health-report-data` topic.
- Serialization uses JSON encoding.

### Avro Producer + Schema
**Files:**
- `Kafka/kafka_producer_avro.py`
- `Kafka/SerDe/health_report.avsc`

- Defines the Avro schema for context/params payloads.
- Sends Avro-encoded records to Kafka with the schema registry.

---

## Data & Configuration

### Food Item Reference Data
**File:** `food_items.xlsx`

- Reference data for `food_items` (serving size, protein, fat, calories).
- Loaded into the database during app startup.

### Docker & Services
**Files:**
- `Dockerfile`
- `docker-compose.yml`

- Dockerfile builds a Streamlit container and starts `healthTrackerAppStreamlit.py`.
- Docker Compose provisions MySQL and Kafka (plus ZooKeeper, Kafka UI, and Schema Registry), and wires the Streamlit service to them.

### Environment & Secrets
**Files:**
- `.env` (not committed; contains API keys and Kafka settings)
- `.streamlit/secrets.toml` (not committed; contains DB credentials)

---

## Supporting/Utility Files

- `requirements.txt`: Python dependencies for the apps and extraction pipeline.
- `mysqlTester.py`: Manual MySQL + Excel connectivity experiments.
- `test_queries.sql`: Example SQL queries for intake and aggregation.
- `health_tracker.db`: A local database artifact (not used by the primary MySQL flow).
- `project_progress_doc.docx`: Historical project notes.

---

## Quick Orientation by Use Case

- **Run the Streamlit app (recommended):** `Dockerfile` + `docker-compose.yml` + `healthTrackerAppStreamlit.py`.
- **Run the Gradio app locally:** `healthTrackerAppGradio.py`.
- **Run the desktop GUI:** `healthTrackerApp.py`.
- **Process health report PDFs:** `medical_extractor_project/` and `Agents/` modules, triggered from Streamlit/Gradio.
- **Publish to Kafka:** `Kafka/` producers with env-configured brokers.
