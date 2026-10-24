"""
Auto Processor - Tự động xử lý MP3 files
Giám sát folder input_mp3, tự động transcribe và dịch
"""

import os
import sys
import time
import glob
import shutil
from pathlib import Path
import logging

import google.generativeai as genai
from threading import Lock

import config
from api_key_manager import get_key_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# PATHS
INPUT_MP3_DIR = config.TRUYEN_INPUT_DIR
PROCESSED_MP3_DIR = config.PROCESSED_MP3_DIR
RAW_SRT_DIR = config.RAW_SRT_DIR
PROCESSED_SRT_DIR = config.PROCESSED_SRT_DIR
PROCESSED_STORIES_DIR = config.PROCESSED_STORIES_DIR


def ensure_dirs():
    """Tạo các thư mục dữ liệu nếu chưa có"""
    for d in [INPUT_MP3_DIR, PROCESSED_MP3_DIR, RAW_SRT_DIR, PROCESSED_SRT_DIR, PROCESSED_STORIES_DIR]:
        os.makedirs(d, exist_ok=True)

# Whisper Model
whisper_model = None
model_lock = Lock()

def get_whisper_model():
    """Load Whisper model"""
    global whisper_model
    if whisper_model is None:
        import whisper  # nặng, chỉ load khi cần transcribe
        logging.info(f"Loading Whisper Model ({config.WHISPER_MODEL})...")
        whisper_model = whisper.load_model(config.WHISPER_MODEL)
    return whisper_model

def format_time(seconds):
    """Format time for SRT"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def split_srt_content(content, max_lines=80):
    """Split SRT content into chunks"""
    blocks = content.strip().split('\n\n')
    chunks = []
    current_chunk = []
    
    for block in blocks:
        current_chunk.append(block)
        if len(current_chunk) >= max_lines:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = []
            
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks

def transcribe_mp3(mp3_path):
    """
    Transcribe MP3 to SRT
    
    Returns:
        (srt_path, srt_content) if success
        (None, None) if failed
    """
    try:
        filename = os.path.basename(mp3_path)
        logging.info(f"🎵 Transcribing: {filename}")
        
        model = get_whisper_model()
        
        # Transcribe
        with model_lock:
            result = model.transcribe(mp3_path)
        
        # Create SRT content
        srt_content = ""
        for i, segment in enumerate(result['segments']):
            srt_content += f"{i + 1}\n"
            srt_content += f"{format_time(segment['start'])} --> {format_time(segment['end'])}\n"
            srt_content += f"{segment['text'].strip()}\n\n"
        
        # Save SRT
        srt_filename = os.path.splitext(filename)[0] + ".srt"
        srt_path = os.path.join(RAW_SRT_DIR, srt_filename)
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        logging.info(f"✅ Transcribed → {srt_filename}")
        
        return srt_path, srt_content
        
    except Exception as e:
        logging.error(f"❌ Transcribe failed for {mp3_path}: {str(e)}")
        return None, None

def process_with_gemini(srt_content, original_filename, max_workers=3):
    """
    Translate SRT with Gemini (PARALLEL translation for chunks)
    Uses API key rotation for better quota management
    
    Returns:
        output_path if success
        None if failed
    """
    try:
        # Get API key from rotation
        key_manager = get_key_manager()
        api_key = key_manager.get_next_key()
        
        if not api_key:
            logging.error("❌ Không có Gemini API key (api_keys.txt hoặc GEMINI_API_KEY)")
            return None
        
        logging.info(f"🤖 Translating with Gemini: {original_filename}")
        logging.info(f"🔑 Using key: {api_key[:8]}...")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        
        prompt = """
        Bạn là dịch giả và biên tập viên chuyên nghiệp. 
        Nhiệm vụ: Chuyển đổi phụ đề (SRT) thành văn bản kể chuyện/thuyết minh tiếng Việt mượt mà.
        
        YÊU CẦU CỰC KỲ QUAN TRỌNG:
        1. CHỈ TRẢ VỀ KẾT QUẢ VĂN BẢN ĐÃ DỊCH. KHÔNG ĐƯỢC có lời dẫn.
        2. Dịch sang Tiếng Việt.
        3. LOẠI BỎ hoàn toàn timestamp và số thứ tự.
        4. GỘP dòng gãy thành câu hoàn chỉnh.
        5. GIỮ NGẮT NGHỈ LOGIC.
        6. VĂN PHONG TỰ NHIÊN (Text-to-Speech).
        7. Nếu gặp TÊN GIỚI THIỆU LẠ (như tên kênh, tên người dẫn chương trình không phổ biến), thay bằng "Will".
        8. Sử dụng "km" thay vì "kilômét" hoặc "ki-lô-mét".
        
        Nội dung SRT:
        """
        
        # Smart chunking: chỉ chunk khi file rất lớn
        # Gemini 2.5 Flash output limit: 8K tokens
        # File 15-20 phút (~500-700 blocks) → ~5K tokens output → OK
        # Chỉ chunk khi > 5000 blocks (file rất dài, >2 giờ)
        
        chunks = split_srt_content(srt_content, max_lines=5000)
        
        if len(chunks) == 1:
            logging.info(f"  File nhỏ ({len(srt_content)} chars), dịch 1 lần không chunk")
        else:
            logging.info(f"  File lớn, chia thành {len(chunks)} chunks")
        
        full_processed_text = [None] * len(chunks)  # Pre-allocate list
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def process_chunk(chunk_info):
            """Process a single chunk"""
            i, chunk = chunk_info
            
            # Create fresh chat for each chunk to avoid rate limits
            chat = model.start_chat(history=[])
            
            if i == 0:
                msg = f"{prompt}\n\n[NỘI DUNG SRT CẦN DỊCH]:\n{chunk}"
            else:
                msg = f"{prompt}\n\n[ĐOẠN {i+1}]:\n{chunk}"
            
            # Retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logging.info(f"  Processing chunk {i+1}/{len(chunks)} (attempt {attempt+1})...")
                    response = chat.send_message(msg)
                    return (i, response.text)
                except Exception as e:
                    logging.warning(f"  Chunk {i+1} retry {attempt+1}/{max_retries}: {str(e)}")
                    if attempt == max_retries - 1:
                        return (i, f"\n[LỖI DỊCH ĐOẠN {i+1}: {str(e)}]\n")
                    time.sleep(2)
        
        # Process chunks in parallel
        logging.info(f"  Translating {len(chunks)} chunks with {max_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_chunk, (i, chunk)): i 
                for i, chunk in enumerate(chunks)
            }
            
            for future in as_completed(futures):
                idx, text = future.result()
                full_processed_text[idx] = text
                logging.info(f"  ✓ Chunk {idx+1}/{len(chunks)} done")
        
        final_text = "\n".join(full_processed_text)
        
        # Save output
        base_name = os.path.splitext(original_filename)[0]
        output_filename = f"{base_name}_dich.txt"
        output_path = os.path.join(PROCESSED_STORIES_DIR, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
        
        logging.info(f"✅ Translated → {output_filename}")
        
        return output_path
        
    except Exception as e:
        logging.error(f"❌ Gemini translation failed: {str(e)}")
        return None

def process_single_mp3(mp3_path):
    """
    Process một MP3 file hoàn chỉnh
    
    Steps:
    1. Transcribe MP3 → SRT
    2. Translate SRT → Vietnamese text
    3. Move MP3 to processed folder
    4. Move SRT to processed folder
    
    Returns:
        True if success, False if failed
    """
    try:
        filename = os.path.basename(mp3_path)
        logging.info(f"\n{'='*60}")
        logging.info(f"📝 PROCESSING: {filename}")
        logging.info(f"{'='*60}")
        
        # Step 1: Transcribe
        srt_path, srt_content = transcribe_mp3(mp3_path)
        
        if not srt_path:
            logging.error(f"❌ Failed to transcribe {filename}")
            return False
        
        # Step 2: Translate
        output_path = process_with_gemini(srt_content, os.path.basename(srt_path), max_workers=3)
        
        if not output_path:
            logging.error(f"❌ Failed to translate {filename}")
            return False
        
        # Step 3: Move MP3 to processed
        processed_mp3_path = os.path.join(PROCESSED_MP3_DIR, filename)
        shutil.move(mp3_path, processed_mp3_path)
        logging.info(f"📦 Moved MP3 → {PROCESSED_MP3_DIR}")
        
        # Step 4: Move SRT to processed
        srt_filename = os.path.basename(srt_path)
        processed_srt_path = os.path.join(PROCESSED_SRT_DIR, srt_filename)
        if os.path.exists(srt_path):
            shutil.move(srt_path, processed_srt_path)
            logging.info(f"📦 Moved SRT → {PROCESSED_SRT_DIR}")
        
        logging.info(f"✅ COMPLETED: {filename}")
        logging.info(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error processing {mp3_path}: {str(e)}")
        return False

def watch_folder(interval=10):
    """
    Giám sát folder input_mp3 và tự động xử lý
    
    Args:
        interval: Số giây giữa mỗi lần scan (default 10s)
    """
    ensure_dirs()
    logging.info("🚀 AUTO PROCESSOR STARTED")
    logging.info(f"📁 Watching: {INPUT_MP3_DIR}")
    logging.info(f"⏱️  Scan interval: {interval}s")
    logging.info(f"{'='*60}\n")
    
    processed_files = set()
    
    while True:
        try:
            # Find all MP3 files
            mp3_files = glob.glob(os.path.join(INPUT_MP3_DIR, "*.mp3"))
            
            # Process new files
            for mp3_path in mp3_files:
                if mp3_path not in processed_files:
                    success = process_single_mp3(mp3_path)
                    
                    if success:
                        processed_files.add(mp3_path)
                    else:
                        # If failed, don't add to processed so it can retry next time
                        logging.warning(f"⚠️ Will retry {os.path.basename(mp3_path)} in next scan")
            
            # Sleep
            time.sleep(interval)
            
        except KeyboardInterrupt:
            logging.info("\n👋 Auto Processor stopped by user")
            break
        except Exception as e:
            logging.error(f"❌ Error in watch loop: {str(e)}")
            time.sleep(interval)

if __name__ == "__main__":
    watch_folder(interval=10)
