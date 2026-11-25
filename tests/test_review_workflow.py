from database.seed import main as seed
from database.database import connect
from services import review_extraction


def test_approved_extraction_updates_parcel_and_audits():
    seed()
    c = connect()
    parcel_id = c.execute('SELECT id FROM parcels LIMIT 1').fetchone()['id']
    document_id = c.execute(
        "INSERT INTO documents(parcel_id,filename,path,mime_type,uploaded_by) VALUES(?,?,?,?,?)",
        (parcel_id, 'fictional.png', 'sample_data/fictional.png', 'image/png', 'revenue'),
    ).lastrowid
    extraction_id = c.execute(
        'INSERT INTO ai_extractions(document_id,field_name,value,confidence,needs_review) VALUES(?,?,?,?,?)',
        (document_id, 'village', 'Corrected Village', .51, 1),
    ).lastrowid
    c.close()
    review_extraction('REVENUE_OFFICER', 'revenue', extraction_id, 'CORRECTED', 'Corrected Village', 'OCR spelling corrected')
    c = connect()
    parcel = c.execute('SELECT village,verification_status FROM parcels WHERE id=?', (parcel_id,)).fetchone()
    audit = c.execute("SELECT action FROM audit_logs WHERE action='FIELD_CORRECTED' ORDER BY id DESC LIMIT 1").fetchone()
    c.close()
    assert parcel['village'] == 'Corrected Village'
    assert parcel['verification_status'] == 'REQUIRES REVIEW'
    assert audit['action'] == 'FIELD_CORRECTED'
