"""
Full Automation Workflow - Tích hợp hoàn toàn
Tải video → Transcribe → Dịch → Tạo Voice - tất cả tự động
"""

import sys
import os
import time
import subprocess
import threading
import glob
from workflow_manager import WorkflowManager
import config

PROCESSED_STORIES_DIR = config.PROCESSED_STORIES_DIR


def start_auto_processor():
    """Start auto processor trong background thread"""
    print("\n🤖 Starting Auto Processor...")
    from auto_processor import watch_folder
    watch_folder(interval=5)  # Check every 5 seconds


def wait_for_translations(expected_count, timeout=3600):
    """
    Chờ cho đến khi có đủ file dịch trong processed_stories
    
    Args:
        expected_count: Số file dịch cần chờ
        timeout: Timeout tối đa (giây), mặc định 1 giờ
    
    Returns:
        Số file dịch đã có
    """
    print(f"\n⏳ Đang chờ {expected_count} file dịch hoàn tất...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        txt_files = glob.glob(os.path.join(PROCESSED_STORIES_DIR, '*_dich.txt'))
        count = len(txt_files)
        
        elapsed = int(time.time() - start_time)
        print(f"\r  📊 Đã dịch: {count}/{expected_count} | ⏱️ {elapsed}s", end="", flush=True)
        
        if count >= expected_count:
            print(f"\n  ✅ Đã có đủ {count} file dịch!")
            return count
        
        time.sleep(10)  # Check mỗi 10 giây
    
    txt_files = glob.glob(os.path.join(PROCESSED_STORIES_DIR, '*_dich.txt'))
    print(f"\n  ⚠️ Timeout! Chỉ có {len(txt_files)}/{expected_count} file")
    return len(txt_files)


def run_voice_generation():
    """Chạy voice generation cho tất cả file đã dịch"""
    from voice_generator import run_batch
    run_batch()


def run_full_automation(batch_size=10):
    """
    Chạy workflow hoàn toàn tự động
    
    1. Download videos từ Sheets
    2. Move files to truyen
    3. Auto transcribe + translate (background)
    4. Tạo voice bằng Vira-TTS
    """
    print("\n" + "="*60)
    print("🚀 FULL AUTOMATION MODE")
    print("="*60)
    print("  Step 1: Download videos từ Google Sheets")
    print("  Step 2: Transcribe (Whisper) + Dịch (Gemini)")
    print("  Step 3: Tạo voice (Vira-TTS clone giọng)")
    print("="*60)
    
    wf = WorkflowManager()
    
    # ===============================
    # Step 1 & 2: Download and move
    # ===============================
    print("\n📥 Step 1: Downloading videos...")
    result = wf.run_full_batch(batch_size=batch_size)
    
    if result['files_moved'] == 0:
        # Kiểm tra nếu đã có file dịch sẵn → chạy voice luôn
        existing_txt = glob.glob(os.path.join(PROCESSED_STORIES_DIR, '*_dich.txt'))
        if existing_txt:
            print(f"\nℹ️ Không có video mới, nhưng có {len(existing_txt)} file dịch sẵn.")
            print("🎤 Chuyển sang tạo voice...\n")
            run_voice_generation()
            return
        
        print("\nℹ️ No new files to process. Exiting.")
        return
    
    print(f"\n✅ Downloaded and moved {result['files_moved']} files")
    
    # ===============================
    # Step 2: Auto processor (transcribe + translate)
    # ===============================
    print("\n🤖 Step 2: Starting Auto Processor (Transcribe + Dịch)...")
    print("="*60)
    
    # Start processor in background
    processor_thread = threading.Thread(target=start_auto_processor, daemon=True)
    processor_thread.start()
    
    # Chờ đủ file dịch
    translated_count = wait_for_translations(
        expected_count=result['files_moved'],
        timeout=3600  # 1 giờ timeout
    )
    
    if translated_count == 0:
        print("\n❌ Không có file dịch nào. Dừng lại.")
        return
    
    # ===============================
    # Step 3: Voice generation (Vira-TTS)
    # ===============================
    print("\n" + "="*60)
    print("🎤 Step 3: Tạo Voice (Vira-TTS)")
    print("="*60)
    
    run_voice_generation()
    
    # ===============================
    # Summary
    # ===============================
    print("\n" + "="*60)
    print("🎉 FULL AUTOMATION HOÀN TẤT!")
    print("="*60)
    print(f"  📥 Videos downloaded: {result['videos_downloaded']}")
    print(f"  📦 Files moved: {result['files_moved']}")
    print(f"  📝 Files translated: {translated_count}")
    print(f"  📂 Output: {config.OUTPUT_DIR}")
    print("="*60)


if __name__ == "__main__":
    import sys
    
    batch_size = 10
    if len(sys.argv) > 1:
        try:
            batch_size = int(sys.argv[1])
        except ValueError:
            print(f"Invalid batch size, using default: {batch_size}")
    
    run_full_automation(batch_size=batch_size)
