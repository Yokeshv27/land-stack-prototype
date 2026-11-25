"""Train the actual local field-label classifier (not a regex substitute)."""
from pathlib import Path
SAMPLES=[('Owner: Ravi Kumar','owner_name'),('Owner Name: Meera Iyer','owner_name'),('Survey Number: 145/2A','survey_number'),('Survey No: 182/1B','survey_number'),('Khasra Number: K-201','khasra_number'),('Khata Number: KH-55','khata_number'),('Area: 2400 sq ft','area'),('Area: 1.5 acres','area'),('Village: Example Village','village'),('District: Chennai','district'),('Tehsil: Example Tehsil','tehsil'),('State: Tamil Nadu','state'),('Land Use: Residential','land_use'),('Registration Number: REG-2026-1','registration_number'),('Mutation Number: MUT-1001','mutation_number'),('Latitude: 13.0827','latitude'),('Longitude: 80.2707','longitude'),('Property Type: Residential Building','property_type'),('Floors: 3','building_floors')]
def train(output=None):
 from sklearn.feature_extraction.text import TfidfVectorizer
 from sklearn.linear_model import LogisticRegression
 from sklearn.pipeline import Pipeline
 import joblib
 x,y=zip(*SAMPLES); model=Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2),lowercase=True)),('classifier',LogisticRegression(max_iter=1000,random_state=42))]); model.fit(x,y)
 output=Path(output or Path(__file__).resolve().parents[1]/'models'/'field_classifier.joblib'); output.parent.mkdir(exist_ok=True); joblib.dump(model,output); return output
if __name__=='__main__': print(f'Wrote {train()}')
