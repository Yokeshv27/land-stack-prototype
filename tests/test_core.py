from auth.security import hash_password,verify_password,allowed
from ulpin.generator import generate
from validation.rules import validate
def test_password_hash(): assert verify_password('safe',hash_password('safe')) and not verify_password('unsafe',hash_password('safe'))
def test_rbac(): assert allowed('ADMIN','audit') and not allowed('CITIZEN','audit')
def test_ulpin_stable():
 g={'type':'Polygon','coordinates':[[[80,13],[81,13],[81,14],[80,13]]]}; assert generate('TN','C','V','1/2A',g)==generate('TN','C','V','1/2A',g)
def test_validation():
 assert validate({'owner_name':'A','survey_number':'1/2A','village':'V','district':'D','state':'S','area':2,'area_unit':'sq_ft','geometry_json':'{}'})[0]['status']=='VALID'
