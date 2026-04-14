"""
Uch Oyoq Bot — Jarima ustidan shikoyat ariza tayyorlovchi Telegram bot.

Ishlash jarayoni:
1. /start → Menyu ko'rsatiladi
2. Foydalanuvchi ariza turini tanlaydi
3. Bot telefon raqamini so'raydi
4. Foydalanuvchi jarima PDF ni yuboradi
5. Bot PDF ni o'qiydi, Gemini AI bilan ma'lumot ajratadi
6. Shablon to'ldiriladi va tayyor PDF qaytariladi
"""

import asyncio
import os
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    FSInputFile, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

import config
from ocr_reader import read_pdf
from extractor import extract_fine_data
from doc_generator import generate_document

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Bot va Dispatcher
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Papkalar yaratish
os.makedirs(config.DOWNLOADS_DIR, exist_ok=True)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)


# ===== FSM HOLATLARI =====
class ArizaForm(StatesGroup):
    """Ariza yaratish bosqichlari."""
    ariza_turi = State()       # Ariza turini tanlash
    shablon_tili = State()     # Shablon tilini tanlash (krill/lotin)
    telefon_raqam = State()    # Telefon raqamini kiritish
    pdf_kutish = State()       # PDF faylni kutish


# ===== KLAVIATURALAR =====
def get_start_keyboard():
    """Bosh menyu tugmalari."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📋 Jarima ustidan shikoyat", 
            callback_data="ariza_jarima"
        )],
        [InlineKeyboardButton(
            text="ℹ️ Bot haqida", 
            callback_data="about"
        )],
    ])


def get_language_keyboard():
    """Til tanlash tugmalari."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🇺🇿 Кирилл (Ўзбекча)", 
            callback_data="til_krill"
        )],
        [InlineKeyboardButton(
            text="🇺🇿 Lotin (O'zbekcha)", 
            callback_data="til_lotin"
        )],
        [InlineKeyboardButton(
            text="⬅️ Ortga", 
            callback_data="ortga_bosh"
        )],
    ])


def get_cancel_keyboard():
    """Bekor qilish tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="❌ Bekor qilish", 
            callback_data="bekor"
        )],
    ])


def get_phone_keyboard():
    """Telefon raqamini yuborish uchun tugma."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="📱 Telefon raqamni yuborish", 
                request_contact=True
            )],
            [KeyboardButton(text="⬅️ Ortga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


# ===== HANDLERLAR =====

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Botni ishga tushirish."""
    await state.clear()
    
    text = (
        "👋 *Assalomu alaykum!*\n\n"
        "Men *Uch Oyoq Jarima Bot* man — yo'l harakati jarimalarini "
        "bekor qilish uchun ariza tayyorlab beraman.\n\n"
        "📄 Siz jarima qarorini PDF formatida yuborsangiz, "
        "men tayyor arizani shakllantirib beraman.\n\n"
        "Quyidagi menyudan tanlang:"
    )
    
    await message.answer(
        text, 
        parse_mode="Markdown",
        reply_markup=get_start_keyboard()
    )


@router.callback_query(F.data == "ariza_jarima")
async def cb_ariza_jarima(callback: types.CallbackQuery, state: FSMContext):
    """Jarima ustidan shikoyat tanlandi."""
    await state.set_state(ArizaForm.shablon_tili)
    await state.update_data(ariza_turi="jarima")
    
    text = (
        "📝 *Jarima ustidan shikoyat*\n\n"
        "Ariza qaysi tilda tayyorlansin?"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_language_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "about")
async def cb_about(callback: types.CallbackQuery):
    """Bot haqida ma'lumot."""
    text = (
        "ℹ️ *Uch Oyoq Jarima Bot*\n\n"
        "Bu bot yo'l harakati jarimalarini bekor qilish uchun "
        "rasmiy ariza tayyorlashga yordam beradi.\n\n"
        "📋 *Ishlash tartibi:*\n"
        "1. Ariza turini tanlaysiz\n"
        "2. Telefon raqamingizni kiritasiz\n"
        "3. Jarima qarorini PDF formatida yuborasiz\n"
        "4. Bot ma'lumotlarni ajratib, tayyor arizani PDF da qaytaradi\n\n"
        "⚖️ Ariza huquqiy asoslarga tayangan holda tayyorlanadi."
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="ortga_bosh")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "ortga_bosh")
async def cb_back_to_start(callback: types.CallbackQuery, state: FSMContext):
    """Bosh menyuga qaytish."""
    await state.clear()
    
    text = (
        "👋 *Assalomu alaykum!*\n\n"
        "Men *Uch Oyoq Jarima Bot* man — yo'l harakati jarimalarini "
        "bekor qilish uchun ariza tayyorlab beraman.\n\n"
        "📄 Siz jarima qarorini PDF formatida yuborsangiz, "
        "men tayyor arizani shakllantirib beraman.\n\n"
        "Quyidagi menyudan tanlang:"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_start_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("til_"), ArizaForm.shablon_tili)
async def cb_til_tanlash(callback: types.CallbackQuery, state: FSMContext):
    """Shablon tili tanlandi."""
    til = callback.data.replace("til_", "")
    await state.update_data(shablon_tili=til)
    await state.set_state(ArizaForm.telefon_raqam)
    
    til_nomi = "Кирилл" if til == "krill" else "Lotin"
    
    text = (
        f"✅ Til tanlandi: *{til_nomi}*\n\n"
        "📱 Endi telefon raqamingizni yuboring yoki qo'lda kiriting.\n\n"
        "_Masalan: +998901234567_"
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.message.answer(
        "Telefon raqamni yuboring:",
        reply_markup=get_phone_keyboard()
    )
    await callback.answer()


@router.message(ArizaForm.telefon_raqam, F.contact)
async def handle_contact(message: types.Message, state: FSMContext):
    """Telefon raqam contact orqali yuborildi."""
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    
    await state.update_data(telefon=phone)
    await state.set_state(ArizaForm.pdf_kutish)
    
    text = (
        f"✅ Telefon raqam qabul qilindi: *{phone}*\n\n"
        "📄 Endi jarima qarorini *PDF* formatida yuboring.\n\n"
        "⚠️ _Faqat .pdf fayl qabul qilinadi_"
    )
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "PDF faylni yuboring:",
        reply_markup=get_cancel_keyboard()
    )


@router.message(ArizaForm.telefon_raqam, F.text)
async def handle_phone_text(message: types.Message, state: FSMContext):
    """Telefon raqam matn sifatida kiritildi."""
    if message.text == "⬅️ Ortga":
        await state.set_state(ArizaForm.shablon_tili)
        await message.answer(
            "📝 Ariza qaysi tilda tayyorlansin?",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(
            "Tilni tanlang:",
            reply_markup=get_language_keyboard()
        )
        return
    
    phone = message.text.strip()
    
    # Telefon raqam validatsiyasi
    import re
    phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
    if not re.match(r'^\+?998\d{9}$', phone_clean):
        await message.answer(
            "❌ Noto'g'ri format. Iltimos, to'g'ri raqam kiriting.\n"
            "_Masalan: +998901234567_",
            parse_mode="Markdown"
        )
        return
    
    if not phone_clean.startswith("+"):
        phone_clean = "+" + phone_clean
    
    await state.update_data(telefon=phone_clean)
    await state.set_state(ArizaForm.pdf_kutish)
    
    text = (
        f"✅ Telefon raqam qabul qilindi: *{phone_clean}*\n\n"
        "📄 Endi jarima qarorini *PDF* formatida yuboring.\n\n"
        "⚠️ _Faqat .pdf fayl qabul qilinadi_"
    )
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "PDF faylni yuboring:",
        reply_markup=get_cancel_keyboard()
    )


@router.callback_query(F.data == "bekor")
async def cb_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Jarayonni bekor qilish."""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Jarayon bekor qilindi.\n\n"
        "Qayta boshlash uchun /start buyrug'ini yuboring."
    )
    await callback.answer()


@router.message(ArizaForm.pdf_kutish, F.document)
async def handle_pdf(message: types.Message, state: FSMContext):
    """PDF fayl qabul qilish va qayta ishlash."""
    
    # Fayl turini tekshirish
    if not message.document.file_name.lower().endswith('.pdf'):
        await message.answer(
            "❌ Faqat *PDF* formatdagi fayllar qabul qilinadi.\n"
            "Iltimos, .pdf fayl yuboring.",
            parse_mode="Markdown"
        )
        return
    
    # Fayl hajmini tekshirish (20 MB max)
    if message.document.file_size > 20 * 1024 * 1024:
        await message.answer("❌ Fayl hajmi 20 MB dan oshmasligi kerak.")
        return
    
    # FSM ma'lumotlarini olish
    fsm_data = await state.get_data()
    shablon_tili = fsm_data.get("shablon_tili", "krill")
    telefon = fsm_data.get("telefon", "")
    
    # Status xabari
    msg = await message.answer("⏳ PDF fayl qabul qilindi. Jarayon boshlandi...")
    
    # Faylni yuklab olish
    file_id = message.document.file_id
    file_name = message.document.file_name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    download_path = os.path.join(config.DOWNLOADS_DIR, f"{timestamp}_{file_name}")
    
    try:
        await msg.edit_text("📥 Fayl yuklab olinmoqda...")
        
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, download_path)
        logger.info(f"Fayl yuklandi: {download_path}")
        
        # 1-bosqich: PDF dan matn o'qish
        await msg.edit_text("🔍 Hujjat matni o'qilmoqda... (1/4)")
        
        text = read_pdf(download_path)
        
        if not text or len(text) < 30:
            await msg.edit_text(
                "❌ Hujjatdan matn o'qib bo'lmadi.\n\n"
                "Iltimos, sifatliroq PDF yuborib ko'ring.\n"
                "Qayta boshlash uchun /start buyrug'ini yuboring."
            )
            await state.clear()
            return
        
        # 2-bosqich: Ma'lumotlarni ajratish
        await msg.edit_text("🤖 Ma'lumotlar AI yordamida ajratilmoqda... (2/4)")
        
        data = extract_fine_data(text)
        
        if not data:
            await msg.edit_text(
                "❌ Hujjatdan ma'lumotlarni ajratib bo'lmadi.\n\n"
                "Ehtimol bu jarima qarori emas yoki format boshqacha.\n"
                "Qayta boshlash uchun /start buyrug'ini yuboring."
            )
            await state.clear()
            return
        
        # Telefon raqamini qo'shish
        data["tel"] = telefon
        
        # 3-bosqich: Hujjat tayyorlash
        await msg.edit_text("📄 Ariza tayyorlanmoqda... (3/4)")
        
        pdf_path = generate_document(data, shablon_tili)
        
        if not pdf_path or not os.path.exists(pdf_path):
            await msg.edit_text(
                "❌ Ariza tayyorlashda xatolik yuz berdi.\n\n"
                "Iltimos, keyinroq urinib ko'ring.\n"
                "Qayta boshlash uchun /start buyrug'ini yuboring."
            )
            await state.clear()
            return
        
        # 4-bosqich: Natijani yuborish
        await msg.edit_text("📤 Tayyor ariza yuborilmoqda... (4/4)")
        
        # Ajratilgan ma'lumotlar haqida xulosa
        summary = _format_summary(data)
        
        await msg.edit_text(
            f"✅ *Ariza tayyor!*\n\n"
            f"{summary}\n\n"
            f"📎 Quyida tayyor arizani yuklab oling:",
            parse_mode="Markdown"
        )
        
        # PDF ni yuborish
        document = FSInputFile(pdf_path, filename=f"Ariza_{data.get('qaror_raqami', 'tayyor')}.pdf")
        await message.answer_document(
            document, 
            caption="📄 Sizning arizangiz tayyor! Sudga topshirishingiz mumkin."
        )
        
        logger.info(f"Ariza yaratildi: {pdf_path} | User: {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Xatolik: {e}", exc_info=True)
        await msg.edit_text(
            "❌ Xatolik yuz berdi.\n\n"
            "Iltimos, keyinroq urinib ko'ring.\n"
            "Qayta boshlash uchun /start buyrug'ini yuboring."
        )
    finally:
        await state.clear()
        # Vaqtinchalik fayllarni tozalash
        _cleanup_file(download_path)


@router.message(ArizaForm.pdf_kutish, F.photo)
async def handle_photo_in_pdf_state(message: types.Message):
    """PDF kutilayotganda rasm yuborildi."""
    await message.answer(
        "📸 Rasm emas, *PDF fayl* yuborishingiz kerak.\n\n"
        "Jarima qarorini PDF formatida yuboring.",
        parse_mode="Markdown"
    )


@router.message(ArizaForm.pdf_kutish)
async def handle_other_in_pdf_state(message: types.Message):
    """PDF kutilayotganda boshqa narsa yuborildi."""
    await message.answer(
        "⚠️ Iltimos, jarima qarorini *PDF fayl* sifatida yuboring.\n\n"
        "Bekor qilish uchun /start buyrug'ini yuboring.",
        parse_mode="Markdown"
    )


@router.message(~StateFilter(None), Command("start"))
async def cmd_start_during_process(message: types.Message, state: FSMContext):
    """Jarayon davomida /start bosildi."""
    await state.clear()
    await cmd_start(message, state)


@router.message()
async def handle_unknown(message: types.Message):
    """Noma'lum xabarlar."""
    await message.answer(
        "🤖 Tushunmadim. Boshlash uchun /start buyrug'ini yuboring."
    )


# ===== YORDAMCHI FUNKSIYALAR =====

def _format_summary(data: dict) -> str:
    """Ajratilgan ma'lumotlar xulosasi."""
    parts = []
    
    if data.get("fish"):
        parts.append(f"👤 *F.I.SH:* {data['fish']}")
    if data.get("qaror_raqami"):
        parts.append(f"📋 *Qaror:* {data['qaror_raqami']}")
    if data.get("qaror_sanasi"):
        parts.append(f"📅 *Sana:* {data['qaror_sanasi']}")
    if data.get("jarima_summasi"):
        parts.append(f"💰 *Jarima:* {data['jarima_summasi']} so'm")
    if data.get("modda"):
        parts.append(f"📖 *Modda:* {data['modda']}")
    if data.get("organ_nomi"):
        parts.append(f"🏢 *Organ:* {data['organ_nomi']}")
    
    return "\n".join(parts) if parts else "Ma'lumotlar ajratildi"


def _cleanup_file(file_path: str):
    """Vaqtinchalik faylni o'chirish."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Tozalandi: {file_path}")
    except Exception as e:
        logger.warning(f"Fayl o'chirishda xatolik: {e}")


# ===== MAIN =====
async def main():
    """Botni ishga tushirish."""
    dp.include_router(router)
    
    logger.info("=" * 50)
    logger.info("Uch Oyoq Bot ishga tushdi!")
    logger.info("=" * 50)
    
    # Eski webhook ni tozalash
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Server portini band qilish (Hosting uchun)
    from keep_alive import keep_alive
    keep_alive()
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
