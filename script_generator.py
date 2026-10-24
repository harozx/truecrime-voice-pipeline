"""
Script Generator - Tạo kịch bản video prompt từ file dịch
Dùng Gemini API để phân tích cốt truyện và tạo prompt cho AI video generation
"""

import os
import sys
import glob
import time
import google.generativeai as genai

import config
from api_key_manager import get_key_manager

# Config
PROCESSED_STORIES_DIR = config.PROCESSED_STORIES_DIR
OUTPUT_DIR = config.OUTPUT_DIR

# Prompt template cho Gemini - 2 Prompt: Ảnh + Chuyển động
SYSTEM_PROMPT = """Bạn là chuyên gia tạo Prompt cho AI Image & Video generation cho kênh True Crime YouTube.

═══ NHIỆM VỤ ═══
Đọc cốt truyện tiếng Việt → Tạo ĐÚNG 2 PROMPT:
- Dòng 1: IMAGE PROMPT (tạo ảnh siêu chân thực)
- Dòng 2: MOTION PROMPT (animate ảnh đó thành video loop 8 giây)

═══ QUY TẮC IMAGE PROMPT ═══

1. NHÂN VẬT THÁM TỬ (BẮT BUỘC CÓ)
   Luôn có 1 thám tử noir. Mặc trench coat dài đen, fedora hat.
   QUAY LƯNG hoặc NGHIÊNG (KHÔNG mặt trực diện).
   Silhouette trong sương/khói/mưa.

2. BỐI CẢNH = BIỂU TƯỢNG CÂU CHUYỆN
   Khung cảnh ám ảnh nhất, đại diện toàn bộ câu chuyện.
   SIÊU CHI TIẾT: vật liệu, kết cấu, màu sắc, dấu vết thời gian.
   Đúng thời đại + quốc gia.

3. CHÂN THỰC TỐI ĐA
   Vật liệu cũ kỹ: gỗ nứt, kim loại rỉ, sơn bong, vải bám bụi.
   Imperfection: vết nứt, mạng nhện, vết ố, nước đọng.
   Ánh sáng tối 70-80%, 1 nguồn sáng chính (chiaroscuro).

4. AN TOÀN NỘI DUNG (AI sẽ reject nếu vi phạm)
   ❌ CẤM: blood, gore, wound, corpse, murder, kill, weapon, gun, knife, violence, torture, suicide, nude
   ✅ THAY: "dark mysterious stains", "signs of disturbance", "disarray", "abandoned scene"
   Tạo rợn bằng: ánh sáng tối, sương mù, bóng đổ, đồ vật xáo trộn, phòng trống, hoang lạnh.

5. TỪ KHÓA CUỐI IMAGE PROMPT:
   Photorealistic, RAW photo, ultra-detailed, shot on Canon EOS R5, 85mm lens, f/1.4, shallow depth of field, volumetric lighting, natural textures, weathered, 35mm film grain, high ISO noise, Kodak Portra 800, cinematic color grading, dark moody atmosphere, 8k resolution. --neg anime, cartoon, 3d render, illustration, painting, digital art, front face, eyes staring, bright lighting, clean, new, modern, oversaturated.

═══ QUY TẮC MOTION PROMPT ═══
Chỉ mô tả 2-3 chuyển động nhẹ, LOOP tự nhiên khi tua ngược:
→ Mưa rơi | Khói bay | Sương mù trôi | Bụi lơ lửng | Đèn nhấp nháy
→ Nến lung lay | Nước nhỏ giọt | Gió thổi rèm | Bóng cây lay | Áo khoác bay nhẹ

═══ VÍ DỤ (THAM KHẢO, KHÔNG COPY) ═══

IMAGE:
A lone detective in a dark trench coat and fedora hat, seen from behind, standing in a dimly lit 1930s hotel room in disarray, overturned furniture, scattered personal belongings on a worn patterned carpet, a rotary telephone off the hook on a dusty nightstand, heavy curtains tightly drawn, dark mysterious stains on crumpled white bed sheets, peeling floral wallpaper with water damage, cobwebs in corners, a single weak brass lamp casting long noir shadows, thick dust particles floating in amber light, atmosphere of abandonment and unresolved mystery, 1930s Kansas City era. Photorealistic, RAW photo, ultra-detailed, shot on Canon EOS R5, 85mm lens, f/1.4, shallow depth of field, volumetric lighting, natural textures, weathered, 35mm film grain, high ISO noise, Kodak Portra 800, cinematic color grading, dark moody atmosphere, 8k resolution. --neg anime, cartoon, 3d render, illustration, painting, digital art, front face, eyes staring, bright lighting, clean, new, modern, oversaturated.

MOTION:
Brass lamp flickering erratically casting wavering shadows, the detective's coat swaying gently, fine dust particles drifting slowly through the amber light beam, a faint draft causing curtains to ripple almost imperceptibly.

═══ OUTPUT (TUYỆT ĐỐI TUÂN THỦ) ═══
CHỈ trả về ĐÚNG 2 đoạn, KHÔNG giải thích, KHÔNG tiếng Việt, KHÔNG label, KHÔNG ghi chú.
Đoạn 1: Image prompt (siêu chi tiết + từ khóa chân thực + negative prompt)
Đoạn 2: Motion prompt (2-3 chuyển động loop)
Ngăn cách 2 đoạn bằng DUY NHẤT 1 dòng trống."""


def generate_script(txt_path):
    """
    Tạo kịch bản video từ 1 file dịch
    
    Args:
        txt_path: Đường dẫn tới file _dich.txt
    
    Returns:
        True nếu thành công
    """
    basename = os.path.splitext(os.path.basename(txt_path))[0]  # e.g. "千田麻未失蹤事件_dich"
    folder_name = basename.replace('_dich', '')
    
    # Xác định output path
    # Ưu tiên output_voice folder nếu có, nếu không thì tạo mới
    output_folder = os.path.join(OUTPUT_DIR, folder_name)
    os.makedirs(output_folder, exist_ok=True)
    
    script_filename = f"{folder_name}_script.txt"
    script_path = os.path.join(output_folder, script_filename)
    
    # Kiểm tra đã tạo script chưa
    if os.path.exists(script_path):
        print(f"  ⏭️ Đã có script: {script_filename}")
        return True
    
    # Đọc nội dung file dịch
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            story_content = f.read().strip()
    except Exception as e:
        print(f"  ❌ Không đọc được file: {e}")
        return False
    
    if not story_content:
        print(f"  ❌ File rỗng: {basename}")
        return False
    
    print(f"\n🎬 Generating script: {folder_name}")
    print(f"  📄 Input: {len(story_content)} chars")
    print(f"  📂 Output: {output_folder}")
    print("-" * 60)
    
    # Lấy API key từ rotation
    key_manager = get_key_manager()
    api_key = key_manager.get_next_key()
    
    if not api_key:
        print("  ❌ Không có API key!")
        return False
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        
        prompt = f"""{SYSTEM_PROMPT}

===== CỐT TRUYỆN =====
{story_content}
===== HẾT CỐT TRUYỆN =====

Viết 2 prompt cho câu chuyện trên: đoạn 1 image, đoạn 2 motion. Không giải thích."""

        start_time = time.time()
        
        response = model.generate_content(
            prompt,
            generation_config={
                'max_output_tokens': 4096,
                'temperature': 0.8,
            }
        )
        
        elapsed = time.time() - start_time
        script_content = response.text
        
        # Lưu script - CHỈ prompt tiếng Anh, không header/giải thích
        # Để mở file → Ctrl+A → Copy → Paste luôn
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content.strip())
        
        print(f"  ✅ Thành công! ({elapsed:.1f}s)")
        print(f"  📄 Saved: {script_filename}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ Lỗi Gemini: {error_msg[:200]}")
        key_manager.report_error(api_key)
        
        # Retry với key khác
        retry_key = key_manager.get_next_key()
        if retry_key and retry_key != api_key:
            print(f"  🔄 Retry với key khác...")
            try:
                genai.configure(api_key=retry_key)
                model = genai.GenerativeModel(config.GEMINI_MODEL)
                
                response = model.generate_content(
                    prompt,
                    generation_config={
                        'max_output_tokens': 8192,
                        'temperature': 0.8,
                    }
                )
                
                script_content = response.text
                
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(script_content.strip())
                
                print(f"  ✅ Retry thành công!")
                return True
            except Exception as e2:
                print(f"  ❌ Retry thất bại: {str(e2)[:100]}")
                return False
        
        return False


def find_txt_files():
    """
    Tìm tất cả file dịch cần tạo script
    Tìm trong cả processed_stories và output_voice
    """
    all_files = []
    
    # Tìm trong processed_stories
    for f in glob.glob(os.path.join(PROCESSED_STORIES_DIR, '*_dich.txt')):
        all_files.append(f)
    
    # Tìm trong output_voice (đã copy vào đây)
    for folder in glob.glob(os.path.join(OUTPUT_DIR, '*')):
        if os.path.isdir(folder):
            for f in glob.glob(os.path.join(folder, '*_dich.txt')):
                # Kiểm tra chưa có script
                folder_name = os.path.basename(folder)
                script_path = os.path.join(folder, f"{folder_name}_script.txt")
                if not os.path.exists(script_path):
                    all_files.append(f)
    
    # Loại bỏ trùng lặp (dùng basename)
    seen = set()
    unique_files = []
    for f in all_files:
        base = os.path.basename(f)
        if base not in seen:
            seen.add(base)
            unique_files.append(f)
    
    return unique_files


def run_batch():
    """Chạy script generation cho tất cả file chưa xử lý"""
    pending = find_txt_files()
    
    if not pending:
        print("ℹ️ Không có file nào cần tạo kịch bản!")
        return
    
    print("=" * 60)
    print("🎬 SCRIPT GENERATOR - True Crime Video Prompts")
    print(f"📂 Output: {OUTPUT_DIR}")
    print(f"📋 Files cần xử lý: {len(pending)}")
    print("=" * 60)
    
    success = 0
    failed = 0
    
    for i, txt_path in enumerate(pending, 1):
        print(f"\n[{i}/{len(pending)}]", end="")
        
        if generate_script(txt_path):
            success += 1
        else:
            failed += 1
        
        # Delay giữa các request để tránh rate limit
        if i < len(pending):
            time.sleep(2)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ:")
    print(f"  ✅ Thành công: {success}/{len(pending)}")
    print(f"  ❌ Thất bại: {failed}/{len(pending)}")
    print(f"  📂 Output: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    run_batch()
