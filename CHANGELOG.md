# Changelog

## [1.0.0] - 2026-10-25

Bản đầu tiên đưa lên git.

### Có sẵn
- Lấy danh sách video từ Google Sheets, tải MP3 song song qua `yt_downloader`.
- Transcribe bằng Whisper, dịch và biên tập thành văn kể chuyện tiếng Việt
  bằng Gemini, xoay vòng nhiều API key.
- Tạo giọng đọc bằng Vira-TTS từ giọng mẫu.
- Tạo prompt ảnh noir và prompt chuyển động loop bằng Gemini.
- Menu `START_HERE.bat` và chế độ chạy tự động toàn bộ.

### Thay đổi khi chuẩn bị phát hành
- Mọi đường dẫn (trước đây cố định ở ổ `E:\`) và thông tin riêng (ID Google
  Sheet, file service account) chuyển sang `.env`; mặc định các dự án đi kèm
  nằm cạnh thư mục này.
- Bỏ Gemini API key viết cứng trong `auto_processor.py`; key chỉ lấy từ
  `api_keys.txt` hoặc biến `GEMINI_API_KEY` (hỗ trợ nhiều key ngăn bằng dấu
  phẩy).
- Log chỉ in 8 ký tự đầu của key.
- Whisper chỉ load khi cần transcribe; model Gemini/Whisper cấu hình được.
- Tạo giọng dừng sớm với thông báo rõ khi thiếu Vira-TTS hoặc giọng mẫu.
- Các file `.bat` chạy được từ bất kỳ vị trí nào.
- Thêm `.env.example`, `api_keys.example.txt`, test và README mới.
