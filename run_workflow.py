"""
CLI Entry Point cho Auto Content Workflow
Giao diện dòng lệnh để điều khiển workflow
"""

from workflow_manager import WorkflowManager
import config


def print_menu():
    """In menu chính"""
    print("\n" + "="*60)
    print("   AUTO CONTENT WORKFLOW - MENU CHÍNH")
    print("="*60)
    print("1. Xem số lượng video chưa làm")
    print("2. Tải 10 video tiếp theo (MP3)")
    print("3. Di chuyển MP3 files sang truyen")
    print("4. Kiểm tra trạng thái files")
    print("5. Chạy full workflow (tải + chuyển)")
    print("6. Thoát")
    print("="*60)


def main():
    """Hàm chính"""
    print("\n🚀 AUTO CONTENT WORKFLOW SYSTEM")
    print("Hệ thống tự động xử lý nội dung từ Google Sheets\n")
    
    wf = WorkflowManager()
    
    while True:
        print_menu()
        choice = input("\nChọn chức năng (1-6): ").strip()
        
        if choice == '1':
            # Xem số lượng video chưa làm
            print("\n" + "="*60)
            print("📊 KIỂM TRA VIDEO CHƯA LÀM")
            print("="*60)
            videos = wf.get_pending_videos(batch_size=config.BATCH_SIZE)
            if videos:
                print(f"\n✅ Có {len(videos)} video đã được đánh dấu 'Not Started'")
            else:
                print("\nℹ️ Không có video nào chưa có trạng thái")
        
        elif choice == '2':
            # Tải 10 video
            print("\n" + "="*60)
            print("📥 TẢI BATCH VIDEOS")
            print("="*60)
            videos = wf.get_pending_videos()
            if videos:
                confirm = input(f"\nTải {len(videos)} video? (y/n): ").strip().lower()
                if confirm == 'y':
                    wf.download_batch(videos)
                else:
                    print("❌ Đã hủy")
            else:
                print("\nℹ️ Không có video để tải")
        
        elif choice == '3':
            # Di chuyển files
            print("\n" + "="*60)
            print("📦 DI CHUYỂN FILES")
            print("="*60)
            moved = wf.move_files_to_truyen()
            if moved > 0:
                print(f"\n✅ Đã chuyển {moved} files")
            else:
                print("\nℹ️ Không có file để chuyển")
        
        elif choice == '4':
            # Kiểm tra trạng thái
            print("\n" + "="*60)
            print("📊 TRẠNG THÁI FILES")
            print("="*60)
            counts = wf.count_pending_files()
            print(f"\n📁 YT Downloader Audio: {counts['yt_downloader_audio']} files")
            print(f"📁 Truyen Input: {counts['truyen_input']} files")
        
        elif choice == '5':
            # Chạy full workflow
            print("\n⚠️ CHUẨN BỊ CHẠY FULL WORKFLOW")
            confirm = input("Xác nhận chạy? (y/n): ").strip().lower()
            if confirm == 'y':
                result = wf.run_full_batch()
                print(f"\n✅ Workflow hoàn tất!")
            else:
                print("❌ Đã hủy")
        
        elif choice == '6':
            # Thoát
            print("\n👋 Cảm ơn đã sử dụng! Tạm biệt!")
            break
        
        else:
            print("\n❌ Lựa chọn không hợp lệ. Vui lòng chọn 1-6.")
        
        input("\nNhấn Enter để tiếp tục...")


if __name__ == "__main__":
    main()
