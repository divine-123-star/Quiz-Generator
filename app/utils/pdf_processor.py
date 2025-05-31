import PyPDF2
import os
from werkzeug.utils import secure_filename

class PDFProcessor:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
    
    def save_pdf(self, file):
        filename = secure_filename(file.filename)
        filepath = os.path.join(self.upload_folder, filename)
        file.save(filepath)
        return filepath
    
    def extract_text(self, filepath):
        text = ""
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text