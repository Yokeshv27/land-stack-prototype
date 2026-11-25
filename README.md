# AI-Powered Land Stack (local hackathon prototype)

This is a functional local demonstration of a parcel-centric Land Stack. It uses SQLite by default, PBKDF2 password hashing, role checks in service/API code, audit logging, a real Tesseract OCR adapter, validation, deterministic **Prototype ULPIN** generation, sample parcel geometry, and a lightweight scikit-learn TF-IDF + Logistic Regression field classifier.

> **Prototype boundary:** sample departments/parcels are mock data. `PROTOTYPE-ULPIN-*` is for demonstration only and is not an officially issued government ULPIN. GIS polygons are not cadastral data. The 3D model is a parameterized Plotly prototype, not LiDAR-derived. No government system is called.

## Run on Windows

```powershell
cd C:\Users\PC3\Documents\Codex\2026-09-02\files-pasted-by-the-user-you\outputs\land_stack_prototype
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m ai.training                 # creates models/field_classifier.joblib
python -m database.seed               # creates data/land_stack.db and sample data
streamlit run app.py
```

Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) separately and either add it to `PATH` or set `TESSERACT_CMD` in `.env`. English (`eng`) is the only shipped OCR language. The app reports an actionable error if it is absent; it does not fabricate OCR output.

Demo accounts: `admin/Admin@123`, `revenue/Revenue@123`, `survey/Survey@123`, `registration/Registration@123`, `tax/Tax@123`, `citizen/Citizen@123`. Change all of these outside demos.

## Demonstration flow

1. Sign in as `revenue`.
2. Open **Document Processing**, select a parcel, and upload a fictional sample document from `sample_data/`.
3. Run local OCR and ML extraction. The application shows raw OCR text plus owner, survey number, area, village, district, latitude, and longitude with confidence scores.
4. Use **Human verification** to approve, correct, or reject an extracted field. AI output is stored separately; the property profile is updated only after approval/correction, and the decision is audited.
5. Open **Property Profile** for readable parcel and departmental data, then **GIS & 3D** for the mock map and 3D building visualization.
6. Sign in as `admin` to review audit history.

## What is implemented vs. future work

| Implemented locally | Prototype/mock boundary | Future production work |
| --- | --- | --- |
| Authentication, RBAC, audit logs, upload checks, OCR adapter, ML classifier, field review, SQLite data, validation, duplicate heuristics, map and 3D view | Sample parcels, fictional documents, mock department records, Prototype ULPIN, illustrative 3D building | Government integrations, official ULPIN, PostGIS, official cadastral data, malware scanning, Indian-language OCR packs, LiDAR/point-cloud processing, managed deployment |

## Repository safety

The included `.gitignore` deliberately excludes `.venv/`, `.env`, `uploads/`, local SQLite databases, and logs. Do **not** commit real land documents or personal data. The files in `sample_data/` are fictional test artifacts only.

## APIs

`uvicorn api:app --reload` exposes `/auth/login`, `/parcels`, `/parcels/{id}/profile`, `/parcels/{id}/gis`, `/parcels/{id}/3d`, `/parcels/{id}/land-stack`, `/documents/upload`, `/ocr/process`, `/ai/extract`, `/validation/run`, and `/audit`. The API uses HTTP Basic authentication for the prototype and applies role checks server-side.

## Tests

```powershell
pytest
```

## Architecture

`database/` owns SQLite schema and seed data; `auth/` owns PBKDF2 and RBAC; `ocr/` performs secure conversion/preprocessing/OCR; `ai/` trains and runs the ML classifier with transparent rule-based value parsers; `services.py` coordinates protected business actions; `gis/`, `ulpin/`, `validation/`, and `visualization/` are independent adapters. Production PostgreSQL/PostGIS, government APIs, language packs, malware scanning, and LiDAR ingestion are documented extension points—not implemented claims.

## Publish to GitHub

```powershell
git init
git add .
git status
git commit -m "Initial Land Stack prototype"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/land-stack-prototype.git
git push -u origin main
```

Create an empty GitHub repository first. Before `git add .`, check `git status` and confirm no files from `uploads/`, `data/`, `.venv/`, or `.env` are listed.
