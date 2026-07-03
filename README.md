# 🎓 Speak Grader

App AI hỗ trợ **giáo viên tiếng Anh chấm bài nói qua video**: chấm điểm theo rubric,
nhận xét điểm mạnh/điểm yếu, gợi ý cải thiện và hướng luyện tập cho từng học sinh —
dùng **Google Gemini**. Chạy cục bộ trên máy bạn (Windows / macOS / Linux), giao diện web.

## Tính năng
- Đưa video (thuyết trình, hỏi–đáp, đối thoại, thảo luận nhóm) → nhận bảng điểm chi tiết.
- 5 rubric mặc định: **IELTS Speaking, CEFR, Cambridge, TOEFL Speaking, Lớp học (thang 10)**.
- Tự tạo **rubric riêng** và lưu lại để tái dùng.
- Tự lấy tên học sinh từ phần tự giới thiệu trong video; nếu không có, đánh nhãn
  "Học sinh 1/2..." để giáo viên gán tên sau.
- Nhận xét bằng **tiếng Việt** (mặc định), tiếng Anh hoặc song ngữ.
- Lưu kết quả vào **SQLite** và **xuất Excel**.

## Lấy API key miễn phí (không cần thẻ, không mua gói)
1. Mở https://aistudio.google.com
2. Đăng nhập tài khoản Google.
3. Bấm **Get API key** → **Create API key**.
4. Copy key.

Model mặc định là **Gemini Flash Lite** — dòng có nhiều lượt miễn phí nhất mỗi ngày,
đủ để chấm cả lớp. Muốn nhận xét tinh tế hơn thì đổi sang **Flash** (chất lượng cao hơn
nhưng ít lượt/ngày hơn). Giới hạn free thay đổi theo tài khoản — xem tại
[AI Studio](https://aistudio.google.com) mục *Rate limits*. Bấm nút **🔄 Tải model** trong app
để lấy đúng danh sách model tài khoản bạn đang có.

Mẹo tiết kiệm quota: để **Độ phân giải video = Thấp** cho video dài (ít token hơn, tránh
vượt giới hạn token/phút của free tier).

## Chạy app

Không cần cài Python thủ công. Script sẽ tự cài `uv` (trình quản lý Python siêu nhẹ)
rồi tự tải đúng thư viện.

**Windows:** double-click `run.bat`

**macOS / Linux:** mở Terminal trong thư mục này rồi:
```bash
./run.sh
```

Lần đầu chạy sẽ:
1. Cài `uv` (nếu chưa có).
2. Tạo file `.env` từ mẫu — **mở `.env` và dán API key của bạn** vào `GEMINI_API_KEY`.
   (Hoặc dán trực tiếp vào ô "Gemini API Key" trên giao diện.)
3. Tải thư viện và mở app trong trình duyệt ở `http://127.0.0.1:7860`.

Chạy lại các lần sau rất nhanh vì thư viện đã có sẵn.

## Cách dùng
1. Chọn video bài nói.
2. Chọn rubric + loại bài + ngôn ngữ nhận xét.
3. (Tùy chọn) gõ tên học sinh, thêm yêu cầu riêng.
4. Bấm **Chấm điểm** → xem kết quả, tải Excel.
5. Xem lại các lần chấm cũ ở tab **Lịch sử**.

## Giới hạn video (Gemini)
- Định dạng: mp4, mov, webm, avi, mpeg, wmv, 3gpp, flv...
- Free tier: tối đa 2GB/file. Video 1 giờ (độ phân giải mặc định) hoặc tới 3 giờ (độ phân giải thấp).
- Gemini lấy mẫu 1 khung hình/giây — hợp với bài nói (không phải hành động nhanh).

## Bảo mật
- App chạy **cục bộ**. API key và video chỉ gửi tới **Google Gemini** để chấm, không tới máy chủ nào khác.
- File video tải lên Gemini **tự xóa sau 48 giờ** (app cũng chủ động xóa ngay sau khi chấm xong).
- File `.env`, cơ sở dữ liệu và Excel kết quả **không** được commit vào git.

## Cấu trúc
```
speak-grader/
├── app.py              # Giao diện Gradio
├── core/
│   ├── gemini_client.py  # Upload File API + gọi chấm điểm
│   ├── schemas.py        # Cấu trúc kết quả (Pydantic)
│   ├── prompts.py        # Dựng prompt
│   ├── rubrics.py        # Rubric mặc định + tùy chỉnh
│   ├── database.py       # SQLite
│   └── export.py         # Xuất Excel
├── data/               # SQLite (tự tạo)
├── exports/            # Excel kết quả
├── run.sh / run.bat    # Khởi động 1 chạm
└── pyproject.toml
```
