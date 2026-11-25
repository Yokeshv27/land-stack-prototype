"""Streamlit UI. All protected actions call service-level RBAC, not merely hidden controls."""
import json
import streamlit as st
from database.seed import main as seed
from services import login, list_parcels, profile, approve, save_extractions, extraction_rows, review_extraction
from ulpin.generator import DISCLAIMER
if 'db_initialized' not in st.session_state:
    seed()
    st.session_state.db_initialized=True
st.set_page_config(page_title='Land Stack',layout='wide')
st.markdown('''<style>.stApp{background:#f5f8fb}.hero{background:#073b4c;color:white;padding:1.2rem;border-radius:12px}.badge{padding:.15rem .5rem;border-radius:8px;background:#d8f3dc}</style>''',unsafe_allow_html=True)
if 'user' not in st.session_state:
 st.markdown('<div class="hero"><h1>Centralized Land Information Platform</h1><p>Local hackathon prototype · mock departmental data</p></div>',unsafe_allow_html=True)
 with st.form('login'):
  u=st.text_input('Username'); p=st.text_input('Password',type='password'); submitted=st.form_submit_button('Sign in')
  if submitted:
   user=login(u,p)
   if user: st.session_state.user=user; st.rerun()
   st.error('Invalid credentials')
 st.info('Demo: revenue / Revenue@123. Demo credentials are listed in README.'); st.stop()
user=st.session_state.user; role=user['role']
with st.sidebar:
 st.title('Land Stack'); page=st.radio('Navigate',['Dashboard','Property Profile','Document Processing','GIS & 3D','Audit'])
 st.caption(f"Signed in as {user['username']} · {role}")
 if st.button('Logout'): st.session_state.clear(); st.rerun()
try:
 parcels=list_parcels(role,public=role=='CITIZEN')
except PermissionError:
 parcels=[]
if page == 'Dashboard':
    st.title('Operational dashboard')
    a, b, c, d = st.columns(4)
    a.metric('Parcels', len(parcels)); b.metric('Verified', sum(x['verification_status']=='VERIFIED' for x in parcels)); c.metric('Pending', sum(x['verification_status']!='VERIFIED' for x in parcels)); d.metric('Departments', 6)
    st.dataframe([{k:x[k] for k in ('id','prototype_ulpin','owner_name','survey_number','village','verification_status') if k in x} for x in parcels], use_container_width=True)
elif not parcels:
    st.warning('Your role has no access to this content.')
else:
    selected=st.selectbox('Select parcel', parcels, format_func=lambda x:f"{x['prototype_ulpin']} — {x['survey_number']}")
    p=profile(role, selected['id'], public=role=='CITIZEN')
    if page == 'Property Profile':
        st.title('Unified Digital Property Profile'); st.warning(DISCLAIMER)
        cols=st.columns(3)
        for col,(label,key) in zip(cols,[('Prototype ULPIN','prototype_ulpin'),('Survey number','survey_number'),('Verification','verification_status')]): col.metric(label,p[key])
        st.subheader('Property details')
        details=[
            ('Owner', p.get('owner_name','Restricted public information')),
            ('Survey number', p.get('survey_number','—')), ('Khasra number',p.get('khasra_number','—')),
            ('Khata number',p.get('khata_number','—')), ('Area',f"{p.get('area','—')} {p.get('area_unit','')}") ,
            ('Village',p.get('village','—')), ('Tehsil',p.get('tehsil','—')), ('District',p.get('district','—')),
            ('State',p.get('state','—')), ('Land use',p.get('land_use','—')), ('Latitude',p.get('latitude','—')),
            ('Longitude',p.get('longitude','—')), ('Building floors',p.get('floors','—'))]
        left,right=st.columns(2)
        for i,(label,value) in enumerate(details):
            (left if i % 2 == 0 else right).markdown(f"**{label}**  \n{value}")
        st.subheader('Linked department information')
        departments=p.get('departments',{})
        if departments:
            for name,values in departments.items():
                with st.expander(name,expanded=name=='Revenue'):
                    st.dataframe([{'Field':key.replace('_',' ').title(),'Value':value} for key,value in values.items()],hide_index=True,use_container_width=True)
        else: st.info('Public profile: linked departmental information is restricted.')
        st.subheader('Validation results'); st.dataframe(p.get('validation',[]),use_container_width=True,hide_index=True)
        if role in ('ADMIN','REVENUE_OFFICER') and st.button('Approve record'):
            approve(role,user['username'],selected['id']); st.success('Record approved and audit event written.')
    elif page == 'Document Processing':
        if role not in ('ADMIN','REVENUE_OFFICER'):
            st.error('RBAC: only an authorized revenue officer may upload/process documents.')
        else:
            f=st.file_uploader('Land record (JPG/JPEG/PNG/TIFF/PDF)',type=['jpg','jpeg','png','tiff','pdf'])
            if f:
                from ocr.engine import validate_upload, ocr
                try:
                    data=f.getvalue(); validate_upload(f.name,data); st.success('Secure type/size checks passed.')
                    if f.type.startswith('image/'): st.image(f)
                    if st.button('Run OCR and extract fields',type='primary'):
                        from pathlib import Path
                        from database.database import connect, audit
                        from ai.extraction import extract
                        uploads=Path('uploads'); uploads.mkdir(exist_ok=True); path=uploads/f"{selected['id']}_{Path(f.name).name}"; path.write_bytes(data)
                        with st.spinner('Reading with Tesseract…'): raw=ocr(path,'eng')
                        if not raw: st.warning('OCR returned no readable text. Try a clearer, upright scan.'); st.stop()
                        c=connect(); cur=c.execute('INSERT INTO documents(parcel_id,filename,path,mime_type,uploaded_by) VALUES(?,?,?,?,?)',(selected['id'],Path(f.name).name,str(path),f.type or 'application/octet-stream',user['username'])); document_id=cur.lastrowid; c.execute('INSERT INTO ocr_results(document_id,raw_text,status) VALUES(?,?,?)',(document_id,raw,'COMPLETE')); c.commit(); c.close()
                        audit(user['username'],role,'DOCUMENT_UPLOAD',selected['id']); audit(user['username'],role,'OCR_PROCESS',selected['id'])
                        st.session_state.latest_ocr=raw; st.session_state.latest_fields=extract(raw); st.session_state.latest_document_id=document_id
                        save_extractions(role,user['username'],document_id,st.session_state.latest_fields)
                    if 'latest_ocr' in st.session_state:
                        with st.expander('Raw OCR text'): st.text(st.session_state.latest_ocr)
                        fields=st.session_state.get('latest_fields',{}); wanted=['owner_name','survey_number','area','village','district','latitude','longitude']
                        rows=[{'Field':key.replace('_',' ').title(),'Extracted value':fields.get(key,{}).get('value','Not found'),'Confidence':f"{fields[key]['confidence']:.0%}" if key in fields else '—','Review':'REQUIRES HUMAN REVIEW' if fields.get(key,{}).get('requires_human_review') else ('Ready to verify' if key in fields else 'Missing')} for key in wanted]
                        st.subheader('Extracted land-record information'); st.dataframe(rows,use_container_width=True,hide_index=True)
                        review_rows=[row for row in extraction_rows(role,selected['id']) if row['document_id']==st.session_state.get('latest_document_id')]
                        if review_rows:
                            st.subheader('Human verification')
                            with st.form('field_review'):
                                item=st.selectbox('Field to review',review_rows,format_func=lambda x:f"{x['field_name'].replace('_',' ').title()}: {x['value']}")
                                decision=st.selectbox('Decision',['APPROVED','CORRECTED','REJECTED'])
                                verified=st.text_input('Verified value',value=item['value'])
                                reason=st.text_input('Reason (required for correction/rejection)')
                                submitted=st.form_submit_button('Save verified field')
                            if submitted:
                                if decision in {'CORRECTED','REJECTED'} and not reason.strip(): st.error('Please record a reason for a correction or rejection.')
                                else:
                                    review_extraction(role,user['username'],item['id'],decision,verified,reason); st.success('Field review saved. The property profile now reflects approved/corrected values.'); st.rerun()
                except (ValueError, RuntimeError) as e: st.error(str(e))
    elif page == 'GIS & 3D':
        st.title('GIS & 3D prototype'); st.info('Mock geometry / parameterized visualization — not cadastral or LiDAR data.')
        try:
            import folium
            from streamlit_folium import st_folium
            m=folium.Map([p['latitude'],p['longitude']],zoom_start=16); folium.GeoJson(p['geometry'],tooltip=p['prototype_ulpin']).add_to(m); st_folium(m,height=380,width=None)
        except ImportError: st.json(p['geometry'])
        st.subheader('3D property prototype')
        try:
            import plotly.graph_objects as go
            coords=p['geometry']['coordinates'][0][:-1]
            # Convert geographic degrees into a local, metre-like coordinate system.
            # Plotly otherwise compares ~0.001 degree footprint width with metres of height.
            raw_x,raw_y=zip(*coords); centre_x=sum(raw_x)/len(raw_x); centre_y=sum(raw_y)/len(raw_y)
            xs=[(x-centre_x)*111_320*0.78 for x in raw_x]
            ys=[(y-centre_y)*110_540 for y in raw_y]
            height=max(int(p.get('floors') or 1),1)*3
            # Four footprint corners extruded into a simple, inspectable building mass.
            fig=go.Figure(go.Mesh3d(
                x=[xs[0],xs[1],xs[2],xs[3],xs[0],xs[1],xs[2],xs[3]],
                y=[ys[0],ys[1],ys[2],ys[3],ys[0],ys[1],ys[2],ys[3]],
                z=[0,0,0,0,height,height,height,height],
                i=[0,0,0,1,2,4,4,4,5,6,0,1], j=[1,2,4,2,3,5,6,7,6,7,4,5], k=[2,3,5,3,0,6,7,0,2,3,5,6],
                color='#1f77b4',opacity=.72,flatshading=True,name='Prototype building'))
            fig.update_layout(height=480,margin=dict(l=0,r=0,t=35,b=0),title=f"{p.get('floors',1)} floors · {height} m prototype height",scene=dict(xaxis_title='Local east-west (m)',yaxis_title='Local north-south (m)',zaxis_title='Height (m)',aspectmode='manual',aspectratio=dict(x=1,y=1,z=.65),camera=dict(eye=dict(x=1.35,y=1.35,z=.95))))
            st.plotly_chart(fig,use_container_width=True)
        except (ImportError, IndexError, KeyError, TypeError) as e:
            st.warning(f'3D view cannot be displayed: {e}')
    elif page == 'Audit':
        if role!='ADMIN': st.error('RBAC: audit logs are restricted to administrators.')
        else:
            from database.database import connect
            c=connect(); st.dataframe([dict(x) for x in c.execute('SELECT * FROM audit_logs ORDER BY id DESC').fetchall()],use_container_width=True); c.close()
