# True Crime Voice Pipeline

Dây chuyền bán tự động biến video kể chuyện vụ án (true crime) tiếng Trung
trên YouTube thành **bản kể tiếng Việt có giọng đọc** và **prompt ảnh/video
AI** cho từng câu chuyện.

```text
Google Sheets ──► yt-dlp (MP3) ──► Whisper (SRT tiếng Trung)
   (danh sách)                         │
                                       ▼
            Gemini: dịch + biên tập thành văn kể chuyện tiếng Việt
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 ▼                                           ▼
     Vira-TTS: đọc bằng giọng mẫu                Gemini: prompt ảnh noir
            (file .wav)                         + prompt chuyển động 8 giây
                 └──────────────► output_voice/<tên truyện>/ ◄┘
```

Mỗi câu chuyện cho ra một thư mục trong `output_voice/`:

| File | Nội dung |
|---|---|
| `<tên>_dich.txt` | Bản kể tiếng Việt, đã bỏ timestamp, câu liền mạch cho TTS |
| `<tên>_dich.wav` | Giọng đọc tạo bằng Vira-TTS từ giọng mẫu |
| `<tên>_script.txt` | 2 đoạn tiếng Anh: prompt ảnh siêu thực (thám tử noir, có negative prompt) và prompt chuyển động loop |

## Thành phần

| File | Vai trò |
|---|---|
| `START_HERE.bat` | Menu chọn chế độ chạy |
| `run_full_automation.py` | Chạy hết: tải → transcribe + dịch → tạo giọng |
| `workflow_manager.py` | Đọc Google Sheets, tải MP3 song song, chuyển file sang `truyen` |
| `run_workflow.py` | Menu dòng lệnh để chạy từng bước |
| `auto_processor.py` | Theo dõi thư mục `input_mp3`, transcribe bằng Whisper và dịch bằng Gemini |
| `voice_generator.py` | Gọi Vira-TTS để đọc các file đã dịch |
| `script_generator.py` | Tạo prompt ảnh + chuyển động bằng Gemini |
| `sheets_reader.py` | Đọc/ghi Google Sheets qua service account |
| `api_key_manager.py` | Xoay vòng nhiều Gemini API key để tăng quota |
| `config.py` | Toàn bộ cấu hình, đọc từ `.env` |

## Yêu cầu

- Windows, Python 3.11
- FFmpeg trong `PATH` (Whisper cần)
- Các dự án đi kèm, mặc định đặt cạnh thư mục này:
  - `../yt_downloader`: module `downloader.Downloader` để tải audio YouTube
  - `../truyen`: thư mục `data/` dùng làm hàng chờ (`input_mp3`,
    `processed_stories`...)
  - `../Vira-tts`: Vira-TTS có `infer.py` và `model_pretrained/`
- Google Cloud service account có quyền Google Sheets API
- Một hoặc nhiều Gemini API key ([hướng dẫn](HUONG_DAN_LAY_GEMINI_API_KEY.md))

## Cài đặt

```bash
pip install -r requirements.txt
copy .env.example .env
copy api_keys.example.txt api_keys.txt
```

1. Điền `SPREADSHEET_ID` và đường dẫn file service account
   (`GOOGLE_CREDENTIALS_FILE`) vào `.env`.
2. Chia sẻ Google Sheet cho email của service account. Chạy
   `python sheets_reader.py` để xem email đó và kiểm tra kết nối.
3. Ghi Gemini API key vào `api_keys.txt`, mỗi dòng một key.
4. Đặt file giọng mẫu ở `voicegoc.MP3`, hoặc chỉ đường dẫn khác bằng
   `VOICE_REF`.
5. Nếu các dự án đi kèm không nằm cạnh thư mục này, sửa `YT_DOWNLOADER_DIR`,
   `TRUYEN_DIR`, `VIRA_TTS_DIR`.

Danh sách đầy đủ biến cấu hình: [`.env.example`](.env.example).

## Google Sheet

Sheet (mặc định tên `OL1`) có các cột:

| A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|
| STT | Link gốc | Tiêu đề gốc | Tiêu đề dịch | Trạng thái | Link video đã làm | Ghi chú |

Mỗi lô (mặc định 10) lấy các dòng có trạng thái `Not Started` và link
YouTube, đổi trạng thái thành `In Progress` rồi tải về.

## Sử dụng

Chạy `START_HERE.bat` và chọn:

| Lựa chọn | Làm gì |
|---|---|
| 1. Full automation | Tải 10 video tiếp theo → transcribe + dịch → tạo giọng |
| 2. Auto processor | Chỉ xử lý MP3 đã có trong `truyen/data/input_mp3` |
| 3. Manual control | Menu từng bước: xem số video, tải, chuyển file |
| 4. Tạo voice | Đọc các file đã dịch bằng Vira-TTS |
| 5. Tạo kịch bản | Tạo prompt ảnh + chuyển động cho các file đã dịch |

Hoặc chạy trực tiếp, ví dụ lô 5 video:

```bash
python run_full_automation.py 5
```

Bước tạo giọng xóa file `_dich.txt` khỏi `processed_stories` sau khi đã
chép vào `output_voice/`. Mỗi bước bỏ qua truyện đã có kết quả, nên có thể
chạy lại khi bị ngắt giữa chừng.

## Kiểm thử

```bash
pip install pytest
python -m pytest tests
```

Test chỉ kiểm tra phần không cần mạng: cấu hình, xoay vòng API key, xử lý SRT.

## Bảo mật

Không commit: `.env`, `api_keys.txt`, file service account `*.json`,
`output_voice/`, file âm thanh. Tất cả đã nằm trong `.gitignore`.

## Lưu ý

- Nội dung nguồn và bản dịch thuộc bản quyền của kênh gốc. Kiểm tra quyền sử
  dụng trước khi đăng lại.
- Chỉ nhái giọng của người đã đồng ý cho dùng giọng mẫu.
- Thư viện `google-generativeai` đã ngừng phát triển; về sau nên chuyển sang
  `google-genai`.
