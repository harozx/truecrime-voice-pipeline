# Hướng Dẫn Lấy Google Gemini API Key

## Bước 1: Truy cập Google AI Studio
🔗 **Link trực tiếp:** https://aistudio.google.com/apikey

## Bước 2: Đăng nhập
- Đăng nhập bằng **Gmail account** của bạn
- Nếu có nhiều Gmail, mở **Incognito/Private window** để đăng nhập từng account

## Bước 3: Tạo API Key

### Cách 1: Tạo nhanh (Khuyến nghị)
1. Click nút **"Get API key"** hoặc **"Create API key"**
2. Chọn **"Create API key in new project"**
3. API key sẽ hiện ra ngay → **Copy và lưu lại**

### Cách 2: Tạo trong project có sẵn
1. Click **"Create API key"**
2. Chọn **Google Cloud project** có sẵn
3. Copy API key

## Bước 4: Lưu trữ API Keys

Tạo file `api_keys.txt` trong thư mục dự án (copy từ `api_keys.example.txt`):

```
# Account 1 - example1@gmail.com
AIzaSyD...key1...

# Account 2 - example2@gmail.com  
AIzaSyD...key2...

# Account 3 - example3@gmail.com
AIzaSyD...key3...
```

⚠️ **LƯU Ý:** `api_keys.txt` đã nằm trong `.gitignore`, không commit file này.
Có thể thay bằng biến `GEMINI_API_KEY` trong `.env` (nhiều key ngăn bằng dấu phẩy).

## Bước 5: Kiểm tra Quota

🔗 **Monitor usage:** https://aistudio.google.com/app/apikey

Quota **miễn phí** cho **gemini-2.5-flash**:
- ✅ 15 requests/phút
- ✅ 1M tokens/phút
- ✅ 1,500 requests/ngày

## Tips Tạo Nhiều Keys

### Dùng nhiều Gmail accounts:
1. Mở nhiều **Incognito windows** (Ctrl+Shift+N)
2. Mỗi tab đăng nhập 1 Gmail khác nhau
3. Vào https://aistudio.google.com/apikey
4. Tạo key cho từng account
5. Copy và lưu vào file

### Tổ chức keys:
```
keys/
  ├─ account1_key.txt
  ├─ account2_key.txt
  └─ account3_key.txt
```

## Quota với Nhiều Keys

| Số Keys | RPM (Request/Phút) | RPD (Request/Ngày) |
|---------|--------------------|--------------------|
| 1 key   | 15                 | 1,500              |
| 3 keys  | 45                 | 4,500              |
| 5 keys  | 75                 | 7,500              |
| 10 keys | 150                | 15,000             |

---

## Links Quan Trọng

- 🔑 **Tạo API Key:** https://aistudio.google.com/apikey
- 📊 **Xem Usage:** https://aistudio.google.com/app/apikey
- 📖 **Docs:** https://ai.google.dev/gemini-api/docs
- 💰 **Pricing:** https://ai.google.dev/pricing

---

## Sau Khi Có Keys

Cho tôi biết bạn có bao nhiêu keys, tôi sẽ giúp implement:
- ✅ Key rotation system (xoay vòng tự động)
- ✅ Load balancing (phân tải)
- ✅ Fallback khi key hết quota
