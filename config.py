"""
Configuration file cho Auto Content System

Mọi đường dẫn và thông tin riêng (ID Google Sheet, file credentials) đọc từ
file .env (xem .env.example). Đường dẫn tương đối được tính từ thư mục dự án.
"""

import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))


def _path(name, default):
    """Đọc đường dẫn từ biến môi trường; đường dẫn tương đối tính từ BASE_DIR"""
    value = os.getenv(name) or default
    return os.path.normpath(os.path.join(BASE_DIR, value))


__version__ = '1.0.0'

# Google Sheets Configuration
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '')
SHEET_NAME = os.getenv('SHEET_NAME', 'OL1')
CREDENTIALS_FILE = _path('GOOGLE_CREDENTIALS_FILE', 'credentials/service_account.json')

# Column indices (0-indexed)
COL_STT = 0              # Cột A - STT
COL_LINK_GOC = 1         # Cột B - Link gốc (tiếng Trung)
COL_TIEU_DE_GOC = 2      # Cột C - Tiêu đề gốc
COL_TIEU_DE_DICH = 3     # Cột D - Tiêu đề dịch tiếng Việt
COL_TRANG_THAI = 4       # Cột E - Trạng thái
COL_LINK_VIDEO_MOI = 5   # Cột F - Link Video mình đã làm
COL_GHI_CHU = 6          # Cột G - Ghi chú

# Status values
STATUS_NOT_STARTED = 'Not Started'
STATUS_IN_PROGRESS = 'In Progress'
STATUS_COMPLETED = 'Completed'

# Dự án bên ngoài (mặc định nằm cạnh thư mục này)
YT_DOWNLOADER_DIR = _path('YT_DOWNLOADER_DIR', '../yt_downloader')
TRUYEN_DIR = _path('TRUYEN_DIR', '../truyen')
VIRA_TTS_DIR = _path('VIRA_TTS_DIR', '../Vira-tts')

# Paths
YT_DOWNLOADER_DOWNLOADS_DIR = os.path.join(YT_DOWNLOADER_DIR, 'downloads')
YT_DOWNLOADER_AUDIO_DIR = os.path.join(YT_DOWNLOADER_DOWNLOADS_DIR, 'youtube', 'audio')
TRUYEN_DATA_DIR = os.path.join(TRUYEN_DIR, 'data')
TRUYEN_INPUT_DIR = os.path.join(TRUYEN_DATA_DIR, 'input_mp3')
PROCESSED_MP3_DIR = os.path.join(TRUYEN_DATA_DIR, 'processed_mp3')
RAW_SRT_DIR = os.path.join(TRUYEN_DATA_DIR, 'raw_srt')
PROCESSED_SRT_DIR = os.path.join(TRUYEN_DATA_DIR, 'processed_srt')
PROCESSED_STORIES_DIR = os.path.join(TRUYEN_DATA_DIR, 'processed_stories')

OUTPUT_DIR = _path('OUTPUT_DIR', 'output_voice')
VOICE_REF = _path('VOICE_REF', 'voicegoc.MP3')
API_KEYS_FILE = _path('API_KEYS_FILE', 'api_keys.txt')
LOG_FILE = _path('LOG_FILE', 'auto_processor.log')

# Models
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')

# Workflow settings
BATCH_SIZE = 10

# Threading settings
MAX_DOWNLOAD_WORKERS = 3  # Số luồng tải song song
MAX_GEMINI_WORKERS = 3    # Số luồng dịch song song
