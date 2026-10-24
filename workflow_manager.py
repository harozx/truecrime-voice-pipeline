"""
Workflow Manager - Orchestrates the entire content automation workflow
"""

import sys
import os
import glob
import shutil
from sheets_reader import SheetsReader
import config

# Add yt_downloader to path
sys.path.insert(0, config.YT_DOWNLOADER_DIR)
from downloader import Downloader  # noqa: E402


class WorkflowManager:
    """Quản lý workflow tự động"""
    
    def __init__(self):
        """Khởi tạo Workflow Manager"""
        print("🚀 Khởi tạo Workflow Manager...\n")
        
        # Initialize components
        self.sheets_reader = SheetsReader(config.CREDENTIALS_FILE)
        self.downloader = Downloader(download_path=config.YT_DOWNLOADER_DOWNLOADS_DIR)
        
        # Paths
        self.audio_source_dir = config.YT_DOWNLOADER_AUDIO_DIR
        self.truyen_input_dir = config.TRUYEN_INPUT_DIR
        
        # Ensure truyen input directory exists
        os.makedirs(self.truyen_input_dir, exist_ok=True)
        
        print("✅ Workflow Manager sẵn sàng!\n")
    
    def get_pending_videos(self, batch_size=None):
        """
        Lấy danh sách video chưa làm từ Google Sheets
        
        Args:
            batch_size: Số lượng video cần lấy (mặc định từ config)
        
        Returns:
            List of video info dicts
        """
        if batch_size is None:
            batch_size = config.BATCH_SIZE
        
        print(f"📊 Đang đọc Google Sheets để tìm {batch_size} video chưa làm...\n")
        
        videos = self.sheets_reader.get_pending_videos(
            config.SPREADSHEET_ID,
            config.SHEET_NAME,
            batch_size=batch_size
        )
        
        if videos:
            print("\n" + "="*60)
            print(f"📋 DANH SÁCH {len(videos)} VIDEO CẦN TẢI:")
            print("="*60)
            for i, video in enumerate(videos, 1):
                print(f"{i}. [STT {video['stt']}] {video['title_vi'][:50]}...")
                print(f"   Link: {video['link']}")
            print("="*60 + "\n")
        
        return videos
    
    def download_batch(self, videos, max_workers=3):
        """
        Tải batch videos dưới dạng MP3 (PARALLEL)
        
        Args:
            videos: List of video info từ get_pending_videos()
            max_workers: Số luồng tải song song (default 3)
        
        Returns:
            Number of successfully downloaded videos
        """
        if not videos:
            print("⚠️ Không có video nào để tải")
            return 0
        
        print(f"\n🎵 BẮT ĐẦU TẢI {len(videos)} MP3 FILES (PARALLEL - {max_workers} workers)...\n")
        print("="*60)
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        
        success_count = 0
        count_lock = threading.Lock()
        
        def download_single(video_info):
            """Download single video with separate downloader instance"""
            idx, video = video_info
            try:
                # Mỗi thread tạo downloader riêng để tránh xung đột
                thread_downloader = Downloader(download_path=config.YT_DOWNLOADER_DOWNLOADS_DIR)
                
                print(f"\n[Thread {threading.current_thread().name}] [{idx}/{len(videos)}] Đang tải: {video['title_vi'][:50]}...")
                print(f"URL: {video['link']}")
                print("-"*60)
                
                thread_downloader.download_audio(video['link'])
                
                print(f"✅ Tải thành công [{idx}/{len(videos)}]")
                return True
            except Exception as e:
                print(f"❌ Lỗi khi tải video {idx}: {str(e)}")
                return False
        
        # Parallel download với ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all downloads
            futures = {
                executor.submit(download_single, (i+1, video)): video 
                for i, video in enumerate(videos)
            }
            
            # Wait for completion
            for future in as_completed(futures):
                if future.result():
                    with count_lock:
                        success_count += 1
        
        print("\n" + "="*60)
        print(f"✅ HOÀN THÀNH: Đã tải thành công {success_count}/{len(videos)} MP3 files")
        print("="*60 + "\n")
        
        return success_count

    
    def move_files_to_truyen(self):
        """
        Di chuyển tất cả MP3 files từ yt_downloader sang truyen
        
        Returns:
            Number of files moved
        """
        print("\n📦 DI CHUYỂN FILES SANG TRUYEN PROJECT...\n")
        
        # Tìm tất cả file MP3 trong thư mục audio
        mp3_pattern = os.path.join(self.audio_source_dir, "*.mp3")
        mp3_files = glob.glob(mp3_pattern)
        
        if not mp3_files:
            print("⚠️ Không tìm thấy file MP3 nào trong thư mục audio")
            return 0
        
        print(f"📁 Tìm thấy {len(mp3_files)} file MP3:")
        
        moved_count = 0
        
        for file_path in mp3_files:
            filename = os.path.basename(file_path)
            destination = os.path.join(self.truyen_input_dir, filename)
            
            try:
                # Check if file already exists
                if os.path.exists(destination):
                    print(f"⚠️ File đã tồn tại, bỏ qua: {filename}")
                    continue
                
                shutil.move(file_path, destination)
                print(f"✅ Đã chuyển: {filename}")
                moved_count += 1
            except Exception as e:
                print(f"❌ Lỗi khi chuyển {filename}: {str(e)}")
        
        print(f"\n✅ Đã chuyển {moved_count}/{len(mp3_files)} files sang {self.truyen_input_dir}\n")
        
        return moved_count
    
    def count_pending_files(self):
        """
        Đếm số file MP3 đang chờ xử lý
        
        Returns:
            Dict with counts for each location
        """
        audio_files = glob.glob(os.path.join(self.audio_source_dir, "*.mp3"))
        truyen_files = glob.glob(os.path.join(self.truyen_input_dir, "*.mp3"))
        
        return {
            'yt_downloader_audio': len(audio_files),
            'truyen_input': len(truyen_files)
        }
    
    def run_full_batch(self, batch_size=None):
        """
        Chạy toàn bộ workflow: đọc sheets → tải → chuyển file
        
        Args:
            batch_size: Số lượng video (mặc định từ config)
        
        Returns:
            Dict with workflow results
        """
        print("\n" + "="*60)
        print("🚀 BẮT ĐẦU WORKFLOW TỰ ĐỘNG")
        print("="*60 + "\n")
        
        # Step 1: Get pending videos
        videos = self.get_pending_videos(batch_size)
        
        if not videos:
            print("ℹ️ Không có video nào cần xử lý. Workflow kết thúc.")
            return {
                'videos_found': 0,
                'videos_downloaded': 0,
                'files_moved': 0
            }
        
        # Step 2: Download videos
        downloaded = self.download_batch(videos, max_workers=config.MAX_DOWNLOAD_WORKERS)
        
        # Step 3: Move files to truyen
        moved = self.move_files_to_truyen()
        
        # Summary
        print("\n" + "="*60)
        print("📊 TÓM TẮT WORKFLOW")
        print("="*60)
        print(f"✅ Videos tìm thấy: {len(videos)}")
        print(f"✅ Videos đã tải: {downloaded}")
        print(f"✅ Files đã chuyển: {moved}")
        print("="*60)
        
        # Next steps
        if moved > 0:
            print("\n📌 BƯỚC TIẾP THEO:")
            print("1. Mở truyen web UI: http://localhost:5000")
            print("2. Click 'Transcribe Audio' để chuyển MP3 → SRT (tiếng Trung)")
            print("3. Click 'Process with Gemini' để dịch sang tiếng Việt")
            print("\nĐể chạy truyen app:")
            print(f"   cd {config.TRUYEN_DIR}")
            print("   python app.py")
            print("="*60 + "\n")
        
        return {
            'videos_found': len(videos),
            'videos_downloaded': downloaded,
            'files_moved': moved
        }


if __name__ == "__main__":
    wf = WorkflowManager()
    
    # Test: Run full batch
    result = wf.run_full_batch()
    
    print("\n✅ Workflow hoàn tất!")
    print(f"Kết quả: {result}")
