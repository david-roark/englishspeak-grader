# 🤝 Hướng dẫn đóng góp vào Speak Grader

Cảm ơn bạn đã quan tâm và muốn đóng góp cho dự án **Speak Grader**! Nhờ sự đóng góp của bạn, dự án sẽ ngày càng hoàn thiện và giúp ích được cho nhiều giáo viên tiếng Anh hơn.

Tài liệu này sẽ hướng dẫn bạn cách thiết lập môi trường phát triển, tuân thủ các tiêu chuẩn viết code (Style Guide) và gửi các đóng góp của mình một cách hiệu quả nhất.

---

## 🚀 Khởi động nhanh (Quick Start)

1. **Fork** repository này về tài khoản GitHub của bạn.
2. **Clone** repository đã fork về máy cá nhân:
   ```bash
   git clone https://github.com/david-roark/englishspeak-grader.git
   cd englishspeak-grader
   ```
3. Tạo một branch mới cho tính năng hoặc sửa lỗi của bạn:
   ```bash
   git checkout -b feature/ten-tinh-nang
   # hoặc
   git checkout -b bugfix/ten-loi
   ```

---

## 🛠️ Thiết lập môi trường phát triển

Dự án sử dụng công cụ **`uv`** để quản lý môi trường ảo (venv) và các thư viện phụ thuộc một cách nhanh chóng và tối ưu.

1. **Cài đặt `uv`** (nếu máy bạn chưa có):
   - Xem hướng dẫn chi tiết tại [Astral uv](https://github.com/astral-sh/uv).
2. **Khởi tạo môi trường ảo**:
   ```bash
   uv venv
   ```
3. **Kích hoạt môi trường ảo**:
   - **Linux/macOS**:
     ```bash
     source .venv/bin/activate
     ```
   - **Windows (Command Prompt)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
4. **Cài đặt các gói phụ thuộc (bao gồm cả thư viện phát triển/dev)**:
   ```bash
   uv pip install -e ".[dev]"
   ```

### Chạy thử ứng dụng ở chế độ Development

Sau khi đã thiết lập môi trường ảo và cài đặt đầy đủ thư viện, bạn có thể khởi chạy ứng dụng Gradio bằng lệnh:

```bash
uv run python app.py
```

Hoặc sử dụng các file script có sẵn tùy thuộc vào hệ điều hành của bạn:

- Windows: chạy `run.bat`
- macOS: chạy `run.command`
- Linux: chạy `./run.sh`

---

## 🧪 Kiểm thử (Testing)

Trước khi commit bất kỳ thay đổi nào hoặc tạo Pull Request, vui lòng chạy toàn bộ bộ kiểm thử để đảm bảo mã của bạn không làm hỏng các tính năng hiện tại.

Chạy lệnh kiểm thử với `pytest`:

```bash
uv run pytest
```

Nếu bạn viết thêm tính năng mới hoặc sửa lỗi phức tạp, vui lòng viết thêm test case tương ứng trong thư mục `tests/`.

---

## 🎨 Quy chuẩn viết Code & Tài liệu (Style Guide)

Để mã nguồn dự án luôn nhất quán và dễ bảo trì, vui lòng tuân thủ các quy tắc sau:

### 1. Code Python

- **Format & Linting**: Khuyên dùng [Ruff](https://github.com/astral-sh/ruff) để tự động định dạng và kiểm tra lỗi cú pháp.
- **Tiêu chuẩn**: Tuân thủ hướng dẫn phong cách code của **PEP 8**.
- **Quy tắc đặt tên**:
  - Tên biến, tên hàm, tên module: sử dụng `snake_case` (ví dụ: `get_gemini_response`, `student_name`).
  - Tên Class: sử dụng `PascalCase` (ví dụ: `GeminiClient`, `ScoreRubric`).
  - Hằng số: viết hoa hoàn toàn `UPPER_CASE` (ví dụ: `DEFAULT_MODEL`, `MAX_RETRIES`).

### 2. Định dạng file Markdown (`.md`)

Khi bạn viết tài liệu hoặc cập nhật các hướng dẫn (như file `README.md` hay `CONTRIBUTING.md` này):

- **Độ dài dòng**: Xuống dòng vật lý (wrap lines) sau mỗi khoảng **100 ký tự**. Việc này giúp cải thiện trải nghiệm đọc code diff trên Git (không phải cuộn ngang để đọc nội dung dài).
- **Cấu trúc Tiêu đề**:
  - Chỉ sử dụng duy nhất một tiêu đề chính cấp 1 (`# Title`) ở đầu file.
  - Sử dụng các tiêu đề cấp dưới (`##`, `###`, `####`) để chia nhỏ các phần.
- **Liên kết (Links)**: Sử dụng định dạng liên kết trực quan của Markdown. Đừng dán link trần trừ khi thực sự cần thiết.
- **Khối Code**: Luôn chỉ định ngôn ngữ lập trình cho khối mã (ví dụ: ` ```python `, ` ```bash `, ` ```markdown `) để kích hoạt syntax highlighting.

### 3. Quy chuẩn viết Commit Message

Dự án khuyến khích sử dụng chuẩn **Conventional Commits**. Mỗi commit message nên có dạng:
`<type>: <description>`

Các `<type>` phổ biến:

- `feat`: Thêm tính năng mới.
- `fix`: Sửa lỗi.
- `docs`: Cập nhật tài liệu hoặc chỉnh sửa file `.md`.
- `style`: Các thay đổi không ảnh hưởng đến logic code (khoảng trắng, format code, thiếu dấu chấm phẩy...).
- `refactor`: Tái cấu trúc mã nguồn nhưng không làm thay đổi tính năng hay sửa lỗi.
- `test`: Thêm hoặc sửa đổi các bộ test case.
- `chore`: Các công việc bảo trì, cập nhật cấu hình build, dependencies...

_Ví dụ:_ `docs: bổ sung quy chuẩn markdown vào contributing guide`

---

## 📬 Quy trình gửi đóng góp (Pull Request Workflow)

1. Đảm bảo toàn bộ test case đã pass (`uv run pytest`).
2. Commit các thay đổi của bạn với commit message rõ ràng.
3. Push branch lên GitHub cá nhân của bạn:
   ```bash
   git push origin feature/ten-tinh-nang
   ```
4. Truy cập vào repository chính trên GitHub và tạo một **Pull Request (PR)**.
5. Mô tả rõ ràng trong PR:
   - Bạn đã thay đổi những gì?
   - Tại sao thay đổi này lại cần thiết?
   - Kết quả test thủ công (nếu có).

Chúng tôi sẽ cố gắng review PR của bạn sớm nhất có thể. Xin chân thành cảm ơn sự đóng góp của bạn!
