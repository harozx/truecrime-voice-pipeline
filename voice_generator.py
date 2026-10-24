"""
Voice Generator - Tạo voice từ file dịch bằng Vira-TTS (voice cloning)
Lấy file _dich.txt từ processed_stories, dùng voicegoc.MP3 để clone giọng,
xuất ra folder riêng gồm cả file txt + wav
"""

import os
import sys
import shutil
import subprocess
import time
import glob

import config

# Config
VIRA_TTS_DIR = config.VIRA_TTS_DIR
VOICE_REF = config.VOICE_REF
PROCESSED_STORIES_DIR = config.PROCESSED_STORIES_DIR
OUTPUT_DIR = config.OUTPUT_DIR  # Folder chứa kết quả


def ensure_dirs():
    """Tạo thư mục output nếu chưa có"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_pending_txt_files():
    """
    Tìm các file _dich.txt chưa được tạo voice
    (Kiểm tra bằng cách xem folder output đã có file .wav tương ứng chưa)
    """
    txt_files = glob.glob(os.path.join(PROCESSED_STORIES_DIR, '*_dich.txt'))
    
    pending = []
    for txt_path in txt_files:
        basename = os.path.splitext(os.path.basename(txt_path))[0]  # e.g. "千田麻未失蹤事件_dich"
        
        # Tạo tên folder output cho file này
        folder_name = basename.replace('_dich', '')
        output_folder = os.path.join(OUTPUT_DIR, folder_name)
        wav_path = os.path.join(output_folder, f"{basename}.wav")
        
        # Nếu chưa có WAV → cần tạo
        if not os.path.exists(wav_path):
            pending.append(txt_path)
    
    return pending


def generate_voice(txt_path):
    """
    Tạo voice cho 1 file txt bằng Vira-TTS
    
    Args:
        txt_path: Đường dẫn tới file _dich.txt
    
    Returns:
        True nếu thành công
    """
    basename = os.path.splitext(os.path.basename(txt_path))[0]  # e.g. "千田麻未失蹤事件_dich"
    folder_name = basename.replace('_dich', '')
    
    # Tạo folder riêng cho mỗi video
    output_folder = os.path.join(OUTPUT_DIR, folder_name)
    os.makedirs(output_folder, exist_ok=True)
    
    # Copy file txt vào folder
    txt_dest = os.path.join(output_folder, os.path.basename(txt_path))
    if not os.path.exists(txt_dest):
        shutil.copy2(txt_path, txt_dest)
        print(f"  📄 Copied txt: {os.path.basename(txt_path)}")
    
    # Output wav path
    wav_filename = f"{basename}.wav"
    wav_path = os.path.join(output_folder, wav_filename)
    
    print(f"\n🎤 Generating voice: {folder_name}")
    print(f"  📄 Input: {os.path.basename(txt_path)}")
    print(f"  🎵 Reference: {os.path.basename(VOICE_REF)}")
    print(f"  📂 Output: {output_folder}")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Gọi Vira-TTS infer.py
        cmd = [
            sys.executable,  # Python hiện tại
            os.path.join(VIRA_TTS_DIR, 'infer.py'),
            '--text-file', txt_path,
            '--reference', VOICE_REF,
            '--output', wav_path,
            '--model', os.path.join(VIRA_TTS_DIR, 'model_pretrained')
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=VIRA_TTS_DIR,
            timeout=600  # 10 phút timeout
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0 and os.path.exists(wav_path):
            wav_size = os.path.getsize(wav_path) / (1024 * 1024)  # MB
            print(f"  ✅ Thành công! ({elapsed:.1f}s, {wav_size:.1f}MB)")
            print(f"  📂 Saved to: {output_folder}")
            
            # Xóa file txt gốc khỏi processed_stories (đã copy vào output folder rồi)
            try:
                os.remove(txt_path)
                print(f"  🗑️ Đã xóa: {os.path.basename(txt_path)} khỏi processed_stories")
            except Exception as e:
                print(f"  ⚠️ Không xóa được file gốc: {e}")
            
            return True
        else:
            print(f"  ❌ Lỗi Vira-TTS:")
            if result.stderr:
                print(f"  {result.stderr[:500]}")
            if result.stdout:
                print(f"  {result.stdout[-500:]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ❌ Timeout sau 10 phút!")
        return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


def run_batch():
    """Chạy voice generation cho tất cả file chưa xử lý"""
    ensure_dirs()

    if not os.path.exists(os.path.join(VIRA_TTS_DIR, 'infer.py')):
        print(f"❌ Không tìm thấy Vira-TTS tại {VIRA_TTS_DIR} (đặt VIRA_TTS_DIR trong .env)")
        return
    if not os.path.exists(VOICE_REF):
        print(f"❌ Không tìm thấy giọng mẫu {VOICE_REF} (đặt VOICE_REF trong .env)")
        return
    
    pending = get_pending_txt_files()
    
    if not pending:
        print("ℹ️ Không có file nào cần tạo voice!")
        return
    
    print("=" * 60)
    print(f"🎤 VOICE GENERATOR - Vira-TTS")
    print(f"📂 Input: {PROCESSED_STORIES_DIR}")
    print(f"🎵 Voice: {os.path.basename(VOICE_REF)}")
    print(f"📦 Output: {OUTPUT_DIR}")
    print(f"📋 Files cần xử lý: {len(pending)}")
    print("=" * 60)
    
    success = 0
    failed = 0
    
    for i, txt_path in enumerate(pending, 1):
        print(f"\n[{i}/{len(pending)}]", end="")
        
        if generate_voice(txt_path):
            success += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ:")
    print(f"  ✅ Thành công: {success}/{len(pending)}")
    print(f"  ❌ Thất bại: {failed}/{len(pending)}")
    print(f"  📂 Output: {OUTPUT_DIR}")
    print("=" * 60)
    
    # List output folders
    if success > 0:
        print("\n📁 Output folders:")
        for folder in sorted(os.listdir(OUTPUT_DIR)):
            folder_path = os.path.join(OUTPUT_DIR, folder)
            if os.path.isdir(folder_path):
                files = os.listdir(folder_path)
                print(f"  📂 {folder}/")
                for f in files:
                    size = os.path.getsize(os.path.join(folder_path, f))
                    print(f"     {'📄' if f.endswith('.txt') else '🎵'} {f} ({size/1024:.1f}KB)")


if __name__ == "__main__":
    run_batch()
