"""
OCR Reader — PDF fayldan matnni ajratib olish moduli.

Strategiya:
1. pdfplumber bilan matn ajratish (raqamli PDF uchun)
2. Agar matn yetarli bo'lmasa — PyMuPDF orqali sahifalarni rasmga aylantirib,
   Gemini Vision API ga yuborib, matn olish (rasmli/skaner PDF uchun)
"""

import os
import io
import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
from google import genai

import config

# Gemini client
client = genai.Client(api_key=config.GEMINI_API_KEY)

MIN_TEXT_LENGTH = 50  # Minimal matn uzunligi — bundan kam bo'lsa OCR ishga tushadi
GEMINI_MODEL = "gemini-2.0-flash-lite"


def extract_text_pdfplumber(file_path: str) -> str:
    """pdfplumber yordamida PDF dan matn ajratish (raqamli PDF uchun)."""
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"pdfplumber xatolik: {e}")
        return ""


def extract_images_from_pdf(file_path: str) -> list:
    """PyMuPDF orqali PDF sahifalarini rasm (PIL Image) sifatida olish."""
    images = []
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Yuqori sifatli rasm olish uchun 2x zoom
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        doc.close()
    except Exception as e:
        print(f"PyMuPDF xatolik: {e}")
    return images


def ocr_with_gemini(images: list) -> str:
    """
    Gemini Vision API orqali rasmlardan matn o'qish.
    Har bir sahifani alohida yuborib, natijalarni birlashtiradi.
    """
    try:
        full_text = ""
        for i, img in enumerate(images):
            prompt = (
                "Bu hujjat sahifasining rasmi. Undagi barcha matnni aynan ko'chirib yoz. "
                "Hech narsa qo'shma va o'zgartirma. Faqat matndagi yozuvlarni qaytar. "
                "Agar krill (kirill) harflari bo'lsa, ularni to'g'ri ko'chir."
            )
            
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt, img]
            )
            
            if response.text:
                full_text += response.text + "\n"
        
        return full_text.strip()
    except Exception as e:
        print(f"Gemini Vision OCR xatolik: {e}")
        return ""


def read_pdf(file_path: str) -> str:
    """
    PDF fayldan matnni o'qish — asosiy funksiya.
    
    1. Avval pdfplumber bilan sinaydi (tez va internet kerak emas)
    2. Agar matn kam bo'lsa — Gemini Vision bilan OCR qiladi
    
    Returns:
        str: PDF dan ajratilgan matn
    """
    if not os.path.exists(file_path):
        print(f"Fayl topilmadi: {file_path}")
        return ""
    
    # 1-qadam: pdfplumber bilan
    text = extract_text_pdfplumber(file_path)
    
    if len(text) >= MIN_TEXT_LENGTH:
        print(f"[OCR] pdfplumber muvaffaqiyatli: {len(text)} belgi")
        return text
    
    # 2-qadam: Gemini Vision bilan OCR
    print("[OCR] pdfplumber matn topmadi, Gemini Vision OCR ishga tushdi...")
    images = extract_images_from_pdf(file_path)
    
    if not images:
        print("[OCR] PDF dan rasmlar ajratib olinmadi")
        return text  # pdfplumber natijasini qaytarish (bo'sh bo'lishi mumkin)
    
    ocr_text = ocr_with_gemini(images)
    
    if ocr_text:
        print(f"[OCR] Gemini Vision muvaffaqiyatli: {len(ocr_text)} belgi")
        return ocr_text
    
    # Hech narsa ishlamadi
    print("[OCR] Matn ajratib olinmadi")
    return text


if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        test_file = os.path.join("downloads", "Jarima qarori.pdf")
    
    result = read_pdf(test_file)
    print("=" * 60)
    print(result[:2000] if result else "Matn topilmadi!")
