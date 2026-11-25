import re
def validate(parcel):
 checks=[]
 def add(field,status,message): checks.append({'field':field,'status':status,'message':message})
 for f in ('owner_name','survey_number','village','district','state'):
  if not parcel.get(f): add(f,'ERROR','Required field is missing')
 if parcel.get('survey_number') and not re.fullmatch(r'\d{1,5}/\d{1,4}[A-Za-z]?',parcel['survey_number']): add('survey_number','WARNING','Unexpected survey-number format')
 if not isinstance(parcel.get('area'),(int,float)) or parcel.get('area',0)<=0: add('area','ERROR','Area must be positive')
 if parcel.get('area_unit') not in {'sq_ft','acre','hectare','sq_m'}: add('area_unit','ERROR','Unsupported area unit')
 if parcel.get('latitude') is not None and not -90<=parcel['latitude']<=90: add('latitude','ERROR','Latitude must be -90..90')
 if parcel.get('longitude') is not None and not -180<=parcel['longitude']<=180: add('longitude','ERROR','Longitude must be -180..180')
 if not parcel.get('geometry_json'): add('geometry','ERROR','Parcel geometry is missing')
 if not checks: add('record','VALID','All local validation rules passed')
 return checks
