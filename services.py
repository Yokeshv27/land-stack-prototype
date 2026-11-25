from database.database import connect, audit
from auth.security import verify_password, require
from validation.rules import validate
from validation.duplicate_detection import find_duplicates
import json
def login(username,password):
 c=connect(); u=c.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone(); c.close()
 if not u or not verify_password(password,u['password_hash']):
  audit(username,'UNKNOWN','LOGIN',status='FAILED'); return None
 audit(username,u['role'],'LOGIN',status='OK'); return dict(u)
def list_parcels(role, public=False):
 require(role,'public_read' if public else 'read'); c=connect(); rows=[dict(x) for x in c.execute('SELECT * FROM parcels').fetchall()]; c.close(); return rows
def profile(role, parcel_id, public=False):
 require(role,'public_read' if public else 'read'); c=connect(); p=c.execute('SELECT * FROM parcels WHERE id=?',(parcel_id,)).fetchone()
 if not p: c.close(); return None
 p=dict(p); p['geometry']=json.loads(p.pop('geometry_json')); p['departments']={x['department']:json.loads(x['payload_json']) for x in c.execute('SELECT * FROM department_records WHERE parcel_id=?',(parcel_id,))}; p['validation']=validate(p); c.close()
 if public: return {k:p[k] for k in ('prototype_ulpin','survey_number','area','area_unit','village','district','state','land_use','verification_status','geometry')}
 return p
def duplicates(role,candidate): require(role,'review'); return find_duplicates(candidate,list_parcels(role))
def approve(role, username, parcel_id):
 require(role,'approve'); c=connect(); before=c.execute('SELECT verification_status FROM parcels WHERE id=?',(parcel_id,)).fetchone(); c.execute("UPDATE parcels SET verification_status='VERIFIED' WHERE id=?",(parcel_id,)); c.commit(); c.close(); audit(username,role,'RECORD_APPROVE',parcel_id,{'status':before['verification_status']},{'status':'VERIFIED'}); return True

PARCEL_FIELD_MAP = {
 'owner_name': 'owner_name', 'survey_number': 'survey_number', 'khasra_number': 'khasra_number',
 'khata_number': 'khata_number', 'village': 'village', 'tehsil': 'tehsil', 'district': 'district',
 'state': 'state', 'land_use': 'land_use', 'latitude': 'latitude', 'longitude': 'longitude', 'area': 'area'
}

def save_extractions(role, username, document_id, fields):
 """Persist ML output separately from official parcel values for human review."""
 require(role, 'review')
 c=connect(); doc=c.execute('SELECT parcel_id FROM documents WHERE id=?',(document_id,)).fetchone()
 if not doc: c.close(); raise ValueError('Document not found')
 c.execute('DELETE FROM ai_extractions WHERE document_id=?',(document_id,))
 for name,item in fields.items():
  c.execute('INSERT INTO ai_extractions(document_id,field_name,value,confidence,needs_review) VALUES(?,?,?,?,?)',(document_id,name,str(item['value']),item['confidence'],int(item['requires_human_review'])))
 c.commit(); c.close(); audit(username,role,'AI_EXTRACTION',doc['parcel_id'],new={'fields':list(fields)},status='OK')

def extraction_rows(role, parcel_id):
 require(role,'review')
 c=connect(); rows=[dict(x) for x in c.execute('''SELECT e.*, d.parcel_id FROM ai_extractions e JOIN documents d ON d.id=e.document_id WHERE d.parcel_id=? ORDER BY e.id DESC''',(parcel_id,))]; c.close(); return rows

def review_extraction(role, username, extraction_id, decision, verified_value=None, reason=''):
 """Approve/correct/reject a field. Only approved/corrected fields update the parcel."""
 require(role,'approve')
 if decision not in {'APPROVED','CORRECTED','REJECTED'}: raise ValueError('Invalid review decision')
 c=connect(); row=c.execute('''SELECT e.*,d.parcel_id FROM ai_extractions e JOIN documents d ON d.id=e.document_id WHERE e.id=?''',(extraction_id,)).fetchone()
 if not row: c.close(); raise ValueError('Extraction not found')
 value = verified_value.strip() if verified_value and decision != 'REJECTED' else (row['value'] if decision == 'APPROVED' else None)
 c.execute('UPDATE ai_extractions SET reviewed_value=?,reviewed_by=?,reviewed_at=CURRENT_TIMESTAMP,reason=? WHERE id=?',(value,username,reason,extraction_id))
 if decision != 'REJECTED' and row['field_name'] in PARCEL_FIELD_MAP:
  column=PARCEL_FIELD_MAP[row['field_name']]
  old=c.execute(f'SELECT {column} FROM parcels WHERE id=?',(row['parcel_id'],)).fetchone()[0]
  if column in {'area','latitude','longitude'}:
   try: value=float(value)
   except (TypeError,ValueError): c.close(); raise ValueError(f'{column} must be numeric')
  c.execute(f'UPDATE parcels SET {column}=?, verification_status=? WHERE id=?',(value,'REQUIRES REVIEW',row['parcel_id']))
  old_value={column:old}; new_value={column:value}
 else: old_value=None; new_value=None
 c.commit(); c.close(); audit(username,role,f'FIELD_{decision}',row['parcel_id'],old_value,new_value,status='OK')
