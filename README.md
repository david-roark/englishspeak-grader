# 🎓 EnglishSpeak Grader

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
- **Tách MP3** từ video (3 mức chất lượng tối ưu cho giọng nói) để lưu trữ hoặc nghe lại.

## Lấy API key miễn phí (không cần thẻ, không mua gói)

1. Mở https://aistudio.google.com
2. Đăng nhập tài khoản Google.
3. Bấm **Get API key** → **Create API key**.
4. Copy key.

Model mặc định là **Gemini Flash Lite** — dòng có nhiều lượt miễn phí nhất mỗi ngày,
đủ để chấm cả lớp. Muốn nhận xét tinh tế hơn thì đổi sang **Flash** (chất lượng cao hơn
nhưng ít lượt/ngày hơn). Giới hạn free thay đổi theo tài khoản — xem tại
[AI Studio](https://aistudio.google.com) mục _Rate limits_. Bấm nút **🔄 Tải model** trong app
để lấy đúng danh sách model tài khoản bạn đang có.

Mẹo tiết kiệm quota: để **Cấp độ quan sát = Thấp** cho video dài (ít token hơn, tránh
vượt giới hạn token/phút của free tier).

## Chạy app

Không cần cài Python thủ công. Script sẽ tự cài `uv` (trình quản lý Python siêu nhẹ)
rồi tự tải đúng thư viện.

| Hệ điều hành | Cách chạy                                         |
| ------------ | ------------------------------------------------- |
| **Windows**  | Double-click `run.bat`                            |
| **macOS**    | Double-click `run.command` trong Finder           |
| **Linux**    | Mở Terminal trong thư mục này rồi chạy `./run.sh` |

> **macOS lần đầu:** nếu double-click báo _"không thể mở vì từ nhà phát triển chưa xác định"_,
> bấm chuột phải vào `run.command` → **Open** → **Open** một lần; các lần sau double-click chạy bình thường.
> Nếu báo _"permission denied"_, mở Terminal trong thư mục này và chạy `chmod +x run.command` một lần.

Lần đầu chạy sẽ:

1. Cài `uv` (nếu chưa có).
2. Tạo file `.env` từ mẫu — **mở `.env` và dán API key của bạn** vào `GEMINI_API_KEY`.
   (Hoặc dán trực tiếp vào ô "Gemini API Key" trên giao diện.)
3. Tải thư viện và mở app trong trình duyệt ở `http://127.0.0.1:7860`.

Chạy lại các lần sau rất nhanh vì thư viện đã có sẵn.

## Tạo shortcut truy cập nhanh

Để khỏi phải mở thư mục mỗi lần, tạo lối tắt (có sẵn icon `icon.ico` / `icon.png` trong thư mục).

**Windows**

1. Chuột phải `run.bat` → **Send to** → **Desktop (create shortcut)**.
2. Chuột phải shortcut vừa tạo → **Properties** → **Change Icon...** → **Browse** → chọn `icon.ico` → OK.
3. (Tùy chọn) Đổi tên shortcut thành _EnglishSpeak Grader_. Có thể kéo vào thanh Taskbar hoặc menu Start để ghim.

**macOS**

1. Kéo `run.command` vào Dock (thả vào phần bên phải, cạnh Thùng rác) để chạy bằng 1 cú nhấp.
2. (Tùy chọn) Đổi icon: chọn `run.command` → **Cmd+I** (Get Info); mở `icon.png`, **Cmd+A** rồi **Cmd+C**; bấm vào icon nhỏ góc trên cửa sổ Get Info rồi **Cmd+V**.

**Linux (GNOME/KDE)**

1. Tạo file `~/.local/share/applications/speak-grader.desktop` với nội dung (sửa `<ĐƯỜNG_DẪN>` thành đường dẫn thật tới thư mục app):
   ```ini
   [Desktop Entry]
   Type=Application
   Name=EnglishSpeak Grader
   Comment=Chấm bài nói tiếng Anh bằng AI
   Exec=<ĐƯỜNG_DẪN>/run.sh
   Icon=<ĐƯỜNG_DẪN>/icon.png
   Terminal=true
   Categories=Education;
   ```
2. Chạy `chmod +x ~/.local/share/applications/speak-grader.desktop`. App sẽ xuất hiện trong menu ứng dụng; kéo ra Desktop hoặc ghim vào thanh tác vụ nếu muốn.

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
englishspeak-grader/
├── app.py              # Giao diện Gradio
├── core/
│   ├── gemini_client.py  # Upload File API + gọi chấm điểm
│   ├── schemas.py        # Cấu trúc kết quả (Pydantic)
│   ├── prompts.py        # Dựng prompt
│   ├── rubrics.py        # Rubric mặc định + tùy chỉnh
│   ├── database.py       # SQLite
│   ├── export.py         # Xuất Excel
│   └── audio.py          # Tách MP3 (ffmpeg đóng gói qua imageio-ffmpeg)
├── data/               # SQLite (tự tạo)
├── exports/            # Excel kết quả
├── run.sh              # Khởi động (Linux)
├── run.command         # Khởi động (macOS, double-click)
├── run.bat             # Khởi động (Windows, double-click)
├── icon.png / icon.ico # Icon cho shortcut
└── pyproject.toml
```
