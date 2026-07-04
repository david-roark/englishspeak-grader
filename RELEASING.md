# 🏷️ Hướng dẫn Quản lý Phiên bản & Release (Dành cho Maintainer)

Tài liệu này hướng dẫn quy trình chuẩn để người duy trì dự án (Maintainer) đánh dấu phiên bản và phát hành các bản Release chính thức trên GitHub cho ứng dụng **EnglishSpeak Grader**.

---

## Quy trình Phát hành Phiên bản mới

Khi bạn đã hoàn thành các tính năng mới hoặc sửa xong các lỗi trong nhánh phát triển và sẵn sàng đóng gói phiên bản mới:

### 1. Cập nhật phiên bản trong mã nguồn

Mở file [pyproject.toml](pyproject.toml) và thay đổi giá trị của trường `version` theo chuẩn [Semantic Versioning](https://semver.org/) (ví dụ: từ `0.1.0` lên `0.1.1` cho các bản vá lỗi nhỏ, hoặc `0.2.0` cho các tính năng mới):

```toml
[project]
name = "englishspeak-grader"
version = "0.1.1"  # Cập nhật số phiên bản tại đây
```

Sau khi sửa xong, lưu lại và commit thay đổi:

```bash
git add pyproject.toml
git commit -m "chore: nâng phiên bản lên v0.1.1"
```

### 2. Tạo Git Tag cục bộ

Tạo một Git Tag có chú thích (Annotated Tag) để đánh dấu điểm release này trên nhánh làm việc hiện tại:

```bash
git tag -a v0.1.1 -m "Mô tả ngắn các tính năng hoặc bản sửa lỗi chính của phiên bản v0.1.1"
```

_(Thay thế `v0.1.1` bằng số phiên bản tương ứng)_

### 3. Đẩy code và tag lên GitHub

Đẩy toàn bộ commit mới cùng tag của bạn lên GitHub:

```bash
# Đẩy code lên nhánh main
git push origin main

# Đẩy tag tương ứng lên GitHub
git push origin v0.1.1
```

### 4. Tạo Release chính thức trên giao diện GitHub

1. Truy cập vào trang dự án của bạn trên GitHub: https://github.com/david-roark/englishspeak-grader
2. Ở cột bên phải trang chủ repository, tìm và bấm chọn mục **Releases** → Bấm nút **Draft a new release**.
3. Tại ô **Choose a tag**, chọn tag `v0.1.1` bạn vừa đẩy lên.
4. Đặt tiêu đề cho Release (ví dụ: `Speak Grader v0.1.1`).
5. Viết nội dung ghi chú phát hành (Release Notes) mô tả danh sách các thay đổi chính, sửa lỗi, hoặc tính năng mới được bổ sung.
6. Bấm nút **Publish release**.

GitHub sẽ tự động tạo gói mã nguồn dạng `.zip` và `.tar.gz` đính kèm theo bản release này cho người dùng tải về.
