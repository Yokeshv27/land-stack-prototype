from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from services import login, list_parcels, profile, save_extractions, review_extraction
from database.seed import main as seed
from auth.security import require
from database.database import connect, audit
from ocr.engine import validate_upload, ocr
from ai.extraction import extract
from validation.rules import validate
from pathlib import Path
seed(); app=FastAPI(title='Land Stack Prototype API'); security=HTTPBasic()
def actor(c:HTTPBasicCredentials=Depends(security)):
 u=login(c.username,c.password)
 if not u: raise HTTPException(401,'Invalid credentials')
 return u
@app.post('/auth/login')
def auth(c:HTTPBasicCredentials=Depends(security)): return actor(c)
@app.get('/parcels')
def parcels(u=Depends(actor)): return list_parcels(u['role'],u['role']=='CITIZEN')
@app.get('/parcels/{parcel_id}/profile')
def parcel_profile(parcel_id:int,u=Depends(actor)):
 p=profile(u['role'],parcel_id,u['role']=='CITIZEN')
 if not p: raise HTTPException(404,'Parcel not found')
 return p
@app.get('/parcels/{parcel_id}/gis')
def gis(parcel_id:int,u=Depends(actor)): return parcel_profile(parcel_id,u)['geometry']
@app.get('/parcels/{parcel_id}/3d')
def three_d(parcel_id:int,u=Depends(actor)): p=parcel_profile(parcel_id,u); return {'floors':p.get('floors'),'height_m':p.get('floors',1)*3,'prototype':True}
@app.get('/parcels/{parcel_id}/land-stack')
def stack(parcel_id:int,u=Depends(actor)): return parcel_profile(parcel_id,u).get('departments',{})
@app.post('/documents/upload')
async def upload(parcel_id:int, file:UploadFile=File(...), u=Depends(actor)):
 try: require(u['role'],'upload')
 except PermissionError as e: raise HTTPException(403,str(e))
 data=await file.read()
 try: validate_upload(file.filename or '',data)
 except ValueError as e: raise HTTPException(400,str(e))
 # Named server-side storage only; input is never executed or opened as code.
 safe=Path(file.filename).name; dest=Path('uploads'); dest.mkdir(exist_ok=True); path=dest/f'{parcel_id}_{safe}'; path.write_bytes(data)
 c=connect(); cur=c.execute('INSERT INTO documents(parcel_id,filename,path,mime_type,uploaded_by) VALUES(?,?,?,?,?)',(parcel_id,safe,str(path),file.content_type or 'application/octet-stream',u['username'])); c.commit(); did=cur.lastrowid; c.close(); audit(u['username'],u['role'],'DOCUMENT_UPLOAD',parcel_id,status='OK')
 return {'document_id':did,'status':'stored'}
@app.post('/ocr/process')
def process_ocr(document_id:int, language:str='eng',u=Depends(actor)):
 try: require(u['role'],'upload')
 except PermissionError as e: raise HTTPException(403,str(e))
 c=connect(); d=c.execute('SELECT * FROM documents WHERE id=?',(document_id,)).fetchone()
 if not d: raise HTTPException(404,'Document not found')
 try: text=ocr(d['path'],language)
 except RuntimeError as e: raise HTTPException(422,str(e))
 cur=c.execute('INSERT INTO ocr_results(document_id,raw_text,status) VALUES(?,?,?)',(document_id,text,'COMPLETE')); c.commit(); c.close(); audit(u['username'],u['role'],'OCR_PROCESS',d['parcel_id'],status='OK'); return {'ocr_result_id':cur.lastrowid,'text':text}
@app.post('/ai/extract')
def ai_extract(ocr_result_id:int,u=Depends(actor)):
 try: require(u['role'],'review')
 except PermissionError as e: raise HTTPException(403,str(e))
 c=connect(); r=c.execute('SELECT o.*,d.parcel_id FROM ocr_results o JOIN documents d ON d.id=o.document_id WHERE o.id=?',(ocr_result_id,)).fetchone()
 if not r: raise HTTPException(404,'OCR result not found')
 try: results=extract(r['raw_text'])
 except RuntimeError as e: raise HTTPException(422,str(e))
 document_id=r['document_id']; c.close(); save_extractions(u['role'],u['username'],document_id,results); return results
class FieldReview(BaseModel):
 decision: str
 verified_value: str | None = None
 reason: str = ''
@app.post('/extractions/{extraction_id}/review')
def review_field(extraction_id:int, body:FieldReview, u=Depends(actor)):
 try: review_extraction(u['role'],u['username'],extraction_id,body.decision,body.verified_value,body.reason)
 except PermissionError as e: raise HTTPException(403,str(e))
 except ValueError as e: raise HTTPException(400,str(e))
 return {'status':'saved','decision':body.decision}
@app.post('/validation/run')
def run_validation(parcel_id:int,u=Depends(actor)):
 p=profile(u['role'],parcel_id); checks=validate(p); c=connect()
 for item in checks: c.execute('INSERT INTO validation_results(parcel_id,field_name,status,message) VALUES(?,?,?,?)',(parcel_id,item['field'],item['status'],item['message']))
 c.commit(); c.close(); return checks
@app.get('/audit')
def get_audit(u=Depends(actor)):
 if u['role']!='ADMIN': raise HTTPException(403,'Audit logs are administrator-only')
 c=connect(); rows=[dict(x) for x in c.execute('SELECT * FROM audit_logs ORDER BY id DESC').fetchall()]; c.close(); return rows
