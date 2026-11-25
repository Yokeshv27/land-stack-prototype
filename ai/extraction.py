"""ML labels each OCR line; transparent parsers then turn a labelled line into a value."""
from pathlib import Path
import re
MODEL=Path(__file__).resolve().parents[1]/'models'/'field_classifier.joblib'
VALUE_PATTERNS={'survey_number':r'\b\d{1,5}/\d{1,4}[A-Za-z]?\b','khasra_number':r'\bK[- ]?\d+\b','khata_number':r'\bKH[- ]?\d+\b','area':r'\b\d+(?:\.\d+)?\s*(?:sq\.?\s*ft|sqft|acres?|hectares?)\b','latitude':r'[-+]?\d{1,2}\.\d+','longitude':r'[-+]?\d{1,3}\.\d+'}
def extract(text:str):
 if not MODEL.exists(): raise RuntimeError('ML model missing. Run: python -m ai.training')
 import joblib
 model=joblib.load(MODEL); results={}
 for line in (x.strip() for x in text.splitlines() if x.strip()):
  label=model.predict([line])[0]; confidence=float(max(model.predict_proba([line])[0])); value=line.split(':',1)[-1].strip()
  match=re.search(VALUE_PATTERNS.get(label,''),value,re.I) if label in VALUE_PATTERNS else None
  if match: value=match.group(0)
  if ':' not in line and not match: continue
  if label not in results or results[label]['confidence']<confidence: results[label]={'value':value,'confidence':round(confidence,3),'requires_human_review':confidence<.80,'source_line':line}
 return results
