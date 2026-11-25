from database.database import init_db, connect
from auth.security import hash_password
from ulpin.generator import generate
import json
USERS={'admin':('Admin@123','ADMIN'),'revenue':('Revenue@123','REVENUE_OFFICER'),'survey':('Survey@123','SURVEY_OFFICER'),'registration':('Registration@123','REGISTRATION_OFFICER'),'tax':('Tax@123','TAX_OFFICER'),'citizen':('Citizen@123','CITIZEN')}
NAMES=['Ravi Kumar','Meera Iyer','Arjun Patel','Lakshmi Devi','Sanjay Rao']
def main():
 init_db(); c=connect()
 # Avoid PBKDF2 work and writes on every UI rerun: demo identities are immutable.
 if not c.execute('SELECT 1 FROM users LIMIT 1').fetchone():
  for u,(p,r) in USERS.items(): c.execute('INSERT OR IGNORE INTO users(username,password_hash,role) VALUES(?,?,?)',(u,hash_password(p),r))
 if not c.execute('SELECT 1 FROM parcels LIMIT 1').fetchone():
  for i,name in enumerate(NAMES,1):
   lat,lon=13.0827+i*.003,80.2707+i*.003; geo={'type':'Polygon','coordinates':[[[lon,lat],[lon+.001,lat],[lon+.001,lat+.001],[lon,lat+.001],[lon,lat]]]}; survey=f'{145+i}/2A'; ulpin=generate('Tamil Nadu','Chennai','Example Village',survey,geo)
   cursor=c.execute('INSERT INTO parcels(prototype_ulpin,owner_name,survey_number,khasra_number,khata_number,area,area_unit,village,tehsil,district,state,land_use,latitude,longitude,geometry_json,verification_status,floors) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(ulpin,name,survey,f'K-{200+i}',f'KH-{50+i}',2400+i*120,'sq_ft','Example Village','Example Tehsil','Chennai','Tamil Nadu','Residential',lat,lon,json.dumps(geo),'VERIFIED',i+1)); pid=cursor.lastrowid
   for dep,payload in {'Revenue':{'mutation':'MUT-'+str(1000+i),'classification':'Patta land'},'Registration':{'number':'REG-2026-'+str(i),'deed_type':'Sale','status':'Registered'},'Tax':{'year':'2026','status':'Paid','outstanding':0},'Building':{'approval':'BP-'+str(i),'floors':i+1,'type':'Residential'},'Land Use':{'category':'Residential'},'Utilities':{'electricity':'Connected','water':'Connected','sewerage':'Available','road_access':'Yes'}}.items(): c.execute('INSERT INTO department_records(parcel_id,department,payload_json) VALUES(?,?,?)',(pid,dep,json.dumps(payload)))
 c.commit(); c.close(); print('Database initialized with 6 users and 5 mock parcels.')
if __name__=='__main__': main()
