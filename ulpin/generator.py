import hashlib, json
DISCLAIMER = "This is a prototype identifier for demonstration only and is not an officially issued government ULPIN."
def generate(state: str, district: str, village: str, survey_number: str, geometry: dict) -> str:
    canonical = json.dumps({"state":state.strip().upper(),"district":district.strip().upper(),"village":village.strip().upper(),"survey":survey_number.strip().upper(),"geometry":geometry}, sort_keys=True, separators=(",",":"))
    return "PROTOTYPE-ULPIN-" + hashlib.sha256(canonical.encode()).hexdigest()[:16].upper()
