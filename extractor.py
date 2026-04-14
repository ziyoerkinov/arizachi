"""
Extractor — PDF matnidan ma'lumotlarni Gemini AI yordamida ajratish moduli.

Gemini API ga matnni yuborib, strukturalangan JSON ma'lumot oladi.
Agar Gemini ishlamasa — eski regex usuli bilan sinaydi.
"""

import re
import json
from google import genai

import config

# Gemini client
client = genai.Client(api_key=config.GEMINI_API_KEY)

GEMINI_MODEL = "gemini-2.0-flash-lite"

GEMINI_PROMPT = """Sen huquqiy hujjatlar bilan ishlaydigan mutaxassis sun'iy intellektsan.
Quyidagi matn yo'l harakati jarima qarori hujjatidan olingan.
Undan quyidagi ma'lumotlarni JSON formatida ajratib ber.

Kerakli maydonlar:
- "fish": F.I.SH (jarima olgan shaxsning to'liq ism-familiya-sharif). Masalan: "Obilov Otamurod Boymurodovich"
- "manzil": Ro'yxatda turgan manzil (viloyat, tuman, ko'cha, uy)
- "qaror_raqami": Qaror raqami (masalan: "SD25700146635" yoki "RK24999617022" - faqat raqam va harflar)
- "qaror_sanasi": Qaror sanasi (DD.MM.YYYY formatida. Masalan: "28.10.2025")
- "modda": Qo'llanilgan modda va qismi (masalan: "128-modda 3-qismi" yoki "128x3-moddasi 1-qismi")
- "jarima_summasi": Jarima summasi (faqat raqam, so'mda. Masalan: "412000")
- "organ_nomi": Jarima chiqargan organ yoki inspektor to'liq nomi (masalan: "Qashqadaryo viloyati MAB inspektori Saidieslombek Shodixonov Murtozaxon o'g'li")
- "tuman_nomi": Tuman yoki shahar nomi (sud uchun). Masalan: "Qamashi tumani" yoki "Navoiy shahri"
- "avtomobil": Avtomobil rusumi (masalan: "Nexia" yoki "Matiz Best")
- "davlat_raqami": Avtomobil davlat raqami (masalan: "85A123BC" yoki "01L827KC")

MUHIM QOIDALAR:
1. Faqat JSON qaytar, boshqa hech narsa yozma
2. Agar biror ma'lumot topilmasa, uning qiymatini "" (bo'sh string) qilib qo'y
3. Matnni o'zbek tilida (lotin yoki krill) bo'lishidan qat'iy nazar, natijani LOTIN alifbosida yoz
4. Ism-familiyalarni har bir so'zning birinchi harfini katta qilib yoz (Title Case)
5. JSON kalit nomlari aynan yuqoridagi kabi bo'lsin

Hujjat matni:
---
{text}
---

JSON natija:"""


def extract_with_gemini(text: str) -> dict:
    """Gemini AI yordamida matndan ma'lumotlarni ajratish."""
    try:
        prompt = GEMINI_PROMPT.format(text=text[:8000])  # Matn uzunligini cheklash
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        response_text = response.text.strip()
        
        # JSON ni tozalash (ba'zan ```json ... ``` ichida keladi)
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            json_lines = []
            inside = False
            for line in lines:
                if line.strip().startswith("```") and not inside:
                    inside = True
                    continue
                elif line.strip() == "```":
                    inside = False
                    continue
                if inside:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)
        
        data = json.loads(response_text)
        
        # Barcha kerakli maydonlarni tekshirish
        required_keys = [
            "fish", "manzil", "qaror_raqami", "qaror_sanasi",
            "modda", "jarima_summasi", "organ_nomi", "tuman_nomi",
            "avtomobil", "davlat_raqami"
        ]
        
        result = {}
        for key in required_keys:
            result[key] = str(data.get(key, "")).strip()
        
        print(f"[Extractor] Gemini natijasi: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
        
    except json.JSONDecodeError as e:
        print(f"[Extractor] Gemini JSON parse xatolik: {e}")
        try:
            print(f"[Extractor] Raw response: {response_text[:500]}")
        except:
            pass
        return None
    except Exception as e:
        print(f"[Extractor] Gemini xatolik: {e}")
        return None


def extract_with_regex(text: str) -> dict:
    """Regex yordamida matndan ma'lumotlarni ajratish (fallback)."""
    text_clean = text.replace('\u2018', "'").replace('\u2019', "'")
    
    # Qaror raqami
    q_raqam = re.search(r"([A-Z]{2}\s?\d{8,15})", text_clean)
    qaror_raqam = q_raqam.group(1).replace(" ", "") if q_raqam else ""
    
    # Qaror sanasi
    q_sana = re.search(r"(\d{2}\.\d{2}\.\d{4})", text_clean)
    qaror_sana = q_sana.group(1) if q_sana else ""
    
    # FIO (turli formatlar)
    a_fio = re.search(r"turuvchi\s+([A-Za-zO'G'\s]+?)\s*\(", text_clean)
    if not a_fio:
        a_fio = re.search(r"mulkdori\s+([A-Za-zO'G'\s]+?)\s*\(", text_clean)
    fish = a_fio.group(1).strip().title() if a_fio else ""
    
    # Manzil
    am_match = re.search(r"([A-Za-zO'G',\s:]+)da\s+ro'yxatda", text_clean)
    manzil = am_match.group(1).strip().title() if am_match else ""
    
    # Modda
    modda_m = re.search(r"(128[\w\.\-]*\s*moddasi\s*\d+-qismida)", text_clean, re.IGNORECASE)
    modda = modda_m.group(1) if modda_m else ""
    
    # Tuman nomi
    tuman_match = re.search(r"([A-Za-zO'G']+)\s+TUMANI", text_clean, re.IGNORECASE)
    tuman_nomi = tuman_match.group(1).title() if tuman_match else ""
    
    # Jarima summasi
    jarima_match = re.search(r"(\d[\d\s]+)\s*so['']?m", text_clean, re.IGNORECASE)
    jarima_summasi = jarima_match.group(1).replace(" ", "") if jarima_match else ""
    
    # Inspektor
    inspektor = re.search(r"men[,\s]+([^\n]+?)(?:maxsus|Ma'muriy)", text_clean, re.IGNORECASE)
    organ_nomi = inspektor.group(1).strip().title() if inspektor else ""
    
    # Avtomobil
    avto = re.search(r"(?:rusumli|rusumi)\s+([A-Za-z0-9\s]+?)(?:\s+davlat|\s+avtomobil)", text_clean, re.IGNORECASE)
    if not avto:
        avto = re.search(r"([A-Za-z\s]+?)\s+rusumli", text_clean, re.IGNORECASE)
    avtomobil = avto.group(1).strip().title() if avto else ""
    
    # Davlat raqami
    dr = re.search(r"(\d{2}[A-Z]\d{3}[A-Z]{2})", text_clean)
    davlat_raqami = dr.group(1) if dr else ""
    
    return {
        "fish": fish,
        "manzil": manzil,
        "qaror_raqami": qaror_raqam,
        "qaror_sanasi": qaror_sana,
        "modda": modda,
        "jarima_summasi": jarima_summasi,
        "organ_nomi": organ_nomi,
        "tuman_nomi": tuman_nomi,
        "avtomobil": avtomobil,
        "davlat_raqami": davlat_raqami
    }


def extract_fine_data(text: str) -> dict:
    """
    Matndan jarima ma'lumotlarini ajratish — asosiy funksiya.
    
    1. Avval Gemini AI bilan sinaydi (aniq va ishonchli)
    2. Agar Gemini ishlamasa — regex bilan sinaydi (fallback)
    
    Args:
        text: PDF dan o'qilgan matn
        
    Returns:
        dict: Ajratilgan ma'lumotlar yoki None
    """
    if not text or len(text) < 20:
        print("[Extractor] Matn juda qisqa yoki bo'sh")
        return None
    
    # 1-qadam: Gemini AI
    data = extract_with_gemini(text)
    
    if data and any(data.values()):
        return data
    
    # 2-qadam: Regex fallback
    print("[Extractor] Gemini ishlamadi, regex ishga tushdi...")
    data = extract_with_regex(text)
    
    if data and any(data.values()):
        return data
    
    return None


if __name__ == "__main__":
    # Test
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    from ocr_reader import read_pdf
    import os
    
    test_file = os.path.join("downloads", "Jarima qarori.pdf")
    if os.path.exists(test_file):
        text = read_pdf(test_file)
        result = extract_fine_data(text)
        if result:
            print("\n" + "=" * 60)
            for k, v in result.items():
                print(f"  {k}: {v}")
        else:
            print("Ma'lumot ajratib bo'lmadi!")
    else:
        print(f"Test fayl topilmadi: {test_file}")
