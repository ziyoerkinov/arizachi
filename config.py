import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Papkalar
DOWNLOADS_DIR = "downloads"
OUTPUT_DIR = "output"
TEMPLATES_DIR = "templates"
