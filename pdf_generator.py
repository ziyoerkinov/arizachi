import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_JUSTIFY

# Ro'yxatdan o'tgan Windows Arial shriftini ishlatamiz (Krill uchun)
def register_fonts():
    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    bold_font_path = "C:\\Windows\\Fonts\\arialbd.ttf"
    if os.path.exists(font_path) and os.path.exists(bold_font_path):
        pdfmetrics.registerFont(TTFont('Arial', font_path))
        pdfmetrics.registerFont(TTFont('Arial-Bold', bold_font_path))
        return True
    return False

def generate_ariza_pdf(data: dict, output_filepath: str):
    has_font = register_fonts()
    font_name = 'Arial' if has_font else 'Helvetica'
    font_bold = 'Arial-Bold' if has_font else 'Helvetica-Bold'
    
    doc = SimpleDocTemplate(
        output_filepath, 
        pagesize=A4,
        rightMargin=40, leftMargin=60,
        topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    style_right = ParagraphStyle(
        'RightLabel', parent=styles['Normal'],
        fontName=font_name, fontSize=12, leading=16,
        alignment=TA_RIGHT
    )
    style_center_title = ParagraphStyle(
        'TitleCenter', parent=styles['Normal'],
        fontName=font_bold, fontSize=14, leading=20,
        alignment=TA_CENTER, spaceAfter=20
    )
    style_justify = ParagraphStyle(
        'JustifyBody', parent=styles['Normal'],
        fontName=font_name, fontSize=12, leading=18,
        alignment=TA_JUSTIFY, spaceAfter=10, firstLineIndent=20
    )
    
    # Ma'lumotlarni dictdan olish (default qiymatlar bilan)
    sud_nomi = data.get('sud_nomi', '________________ тумани судига')
    arizachi_fio = data.get('arizachi_fio', "__________________ дан")
    arizachi_manzil = data.get('arizachi_manzil', "__________________")
    arizachi_tel = data.get('arizachi_tel', "__________________")
    
    inspector_fio = data.get('inspector_fio', "__________________")
    qaror_sana = data.get('qaror_sana', "____ йил __________ даги")
    qaror_raqam = data.get('qaror_raqam', "____________-сонли")
    modda = data.get('modda', "МЖтКнинг 128-моддаси")
    
    elements = []
    
    # HEADER
    elements.append(Paragraph(f"Жиноят ишлари бўйича {sud_nomi} судига", style_right))
    elements.append(Paragraph(f"{arizachi_fio} дан", style_right))
    elements.append(Paragraph(f"<b>Манзил:</b> {arizachi_manzil}", style_right))
    elements.append(Paragraph(f"<b>Тел:</b> {arizachi_tel}", style_right))
    elements.append(Spacer(1, 40))
    
    # TITLE
    elements.append(Paragraph("А Р И З А", style_center_title))
    elements.append(Paragraph("(ЙҲХБ қарорини бекор қилиб, иш юритишни тугатиш тўғрисида)", ParagraphStyle('TitleSub', parent=style_center_title, fontName=font_name, fontSize=12)))
    elements.append(Spacer(1, 20))
    
    # BODY PARAGRAPHS
    p1 = f"{inspector_fio}нинг {qaror_sana} кунидаги {qaror_raqam} жарима солиш тўғрисидаги қарорига кўра махсус автоматлаштирилган фото ва видео қайд этиш техника воситалари орқали қайд этилган қоида бузилиши кўриб чиқилиб, {modda} 3-қисмига асосан мени айбдор деб топиб жарима қўлланилган. Ушбу ҳуқуқбузарлик махсус автоматлаштирилган фото ва видео қайд этиш тизими (стационар) орқали аниқланганлиги баён этилган."
    elements.append(Paragraph(p1, style_justify))
    
    p2 = "Ушбу жарима солиш тўғрисидаги қарор Ўзбекистон Республикасининг амалдаги қонунчилик талаблари қўпол равишда бузилган ҳолда расмийлаштирилган ва қуйидаги асосларга кўра бекор қилиниши лозим:"
    elements.append(Paragraph(p2, style_justify))
    
    p3 = "Биринчидан, Вазирлар Маҳкамасининг 2018 йил 1 декабрдаги 975-сон қарорига мувофиқ қабул қилинган низомнинг 37-бандида ҳам «Жарима солиш тўғрисидаги қарор махсус автоматлаштирилган фото ва видео қайд этиш техника воситалари қўлланилган ҳолда олинган материаллар илова қилиниб, юридик кучга эга бўлган электрон ҳужжат шаклида расмийлаштирилади ҳамда ушбу ҳужжатни тузган ваколатли шахснинг электрон рақамли имзоси билан тасдиқланади» деб белгиланган. Юқоридаги қарорда эса ҳеч қандай электрон рақамли имзо мавжуд эмас. Қонунчиликка мувофиқ, тегишли тартибда тасдиқланмаган ҳужжат юридик кучга эга бўлмайди ва ноқонуний ҳисобланади."
    elements.append(Paragraph(p3, style_justify))
    
    p4 = "Иккинчидан, низомнинг 28-бандига кўра рухсат этилмаган ёки сертификати йўқ мосламалардан олинган жарималар юридик кучга эга эмас. Йўл ҳаракати ҳужжатида техниканинг қонунийлиги ва сертификати бириктирилмаган."
    elements.append(Paragraph(p4, style_justify))

    p5 = "Учинчидан, низомнинг 41-бандига кўра ЙПХ ходими йўлларда хизматни яширин олиб бориши тақиқланади. Радар кўриниши ҳамда огоҳлантирувчи белгилар бўлиши шарт. Бироқ мазкур ишда хизмат кўрсатиш яширин равишда олиб борилганлиги эҳтимоли юқори."
    elements.append(Paragraph(p5, style_justify))
    
    p6 = "Тўртинчидан, ВМ 2024 йил 25 мартдаги 148-сон қарори 2-иловасига кўра 6 ± 10 сониядан иборат видеолавҳа бўлиши шарт. Қарорда бу очиқ кўрсатилмаган. Бешинчидан, 2025 йил 1 сентябрдан 318-сонли қарорга кўра 250-500 метр оралиғида 'Радар' белгиси ўрнатилиши мажбурий. Холатда белги кўйилмаган эди."
    elements.append(Paragraph(p6, style_justify))
    
    p7 = "Юқоридагиларга кўра, Конституциянинг 20-моддаси ва МЖтКнинг 171, 271, 283, 309(1), 321-моддаларига асосан,"
    elements.append(Paragraph(p7, style_justify))
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("С Ў Р А Й М А Н :", style_center_title))
    
    p_sura = f"{inspector_fio}нинг {qaror_sana} кунидаги {qaror_raqam} қарорини бекор қилишингизни."
    elements.append(Paragraph(p_sura, style_justify))
    elements.append(Spacer(1, 30))
    
    style_left = ParagraphStyle('Left', parent=style_justify, firstLineIndent=0)
    elements.append(Paragraph("<b>Илова :</b>", style_left))
    elements.append(Paragraph("- Жарима солиш тўғрисидаги қарор нусхаси;", style_left))
    elements.append(Paragraph("- Ҳайдовчилик гувоҳномаси нусхаси;", style_left))
    elements.append(Paragraph("- Автомототранспорт воситаси рўйхатдан ўтказилганлиги тўғрисидаги гувоҳнома нусхаси;", style_left))
    elements.append(Paragraph("- Шахсни тасдиқловчи ҳужжат (паспорт/ID карта) нусхаси.", style_left))
    
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(f"<b>Аризачи:</b> ___________________ {arizachi_fio}", style_right))
    elements.append(Paragraph(f"<b>Сана:</b> ___________________", style_right))

    doc.build(elements)
    
if __name__ == "__main__":
    # Test uchun
    test_data = {
        "sud_nomi": "Қамаши",
        "arizachi_fio": "Обилов Отамурод Боймуродович",
        "arizachi_manzil": "Қашқадарё вилояти, Қамаши тумани",
        "arizachi_tel": "+998 90 123 45 67",
        "inspector_fio": "Қашқадарё вилояти МАБ инспектори С.Шодихонов",
        "qaror_sana": "28.10.2025",
        "qaror_raqam": "SD25700146635-сонли",
        "modda": "МЖтКнинг 128-моддаси"
    }
    generate_ariza_pdf(test_data, "test_ariza.pdf")
    print("Test PDF yaratildi.")
