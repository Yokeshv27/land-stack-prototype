from pathlib import Path
ALLOWED={'.jpg','.jpeg','.png','.tiff','.pdf'}; MAX_BYTES=10*1024*1024
def validate_upload(name, data):
 suffix=Path(name).suffix.lower()
 if suffix not in ALLOWED: raise ValueError('Unsupported file type')
 if not data or len(data)>MAX_BYTES: raise ValueError('File is empty or exceeds 10 MB')
 return suffix
def ocr(path, language='eng'):
 try:
  import pytesseract
  from PIL import Image, ImageOps, ImageFilter
 except ImportError as e: raise RuntimeError('Install pytesseract and Pillow to use OCR') from e
 try:
  path=Path(path)
  if path.suffix.lower()=='.pdf':
   try:
    import fitz  # PyMuPDF
    pdf=fitz.open(path); pages=[Image.open(__import__('io').BytesIO(page.get_pixmap(matrix=fitz.Matrix(2,2)).tobytes('png'))) for page in pdf]
   except Exception as e: raise RuntimeError('PDF OCR needs the PyMuPDF dependency and a readable PDF.') from e
  else: pages=[Image.open(path)]
  text=[]
  for img in pages:
   img=ImageOps.grayscale(img).filter(ImageFilter.MedianFilter(3)); img=ImageOps.autocontrast(img)
   text.append(pytesseract.image_to_string(img,lang=language))
  return '\n'.join(text).strip()
 except pytesseract.TesseractNotFoundError as e: raise RuntimeError('Tesseract is not installed or not on PATH. See README.') from e
