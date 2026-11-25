from difflib import SequenceMatcher
def find_duplicates(candidate, parcels):
 hits=[]
 for p in parcels:
  score=sum([candidate.get('survey_number','').lower()==p['survey_number'].lower(),candidate.get('village','').lower()==p['village'].lower(),SequenceMatcher(None,candidate.get('owner_name','').lower(),p['owner_name'].lower()).ratio()>.85,candidate.get('district','').lower()==p['district'].lower()])/4
  if score>=.5: hits.append({'parcel_id':p['id'],'prototype_ulpin':p['prototype_ulpin'],'similarity':round(score*100)})
 return hits
