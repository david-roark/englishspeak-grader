#!/usr/bin/env bash
# Chạy Speak Grader trên macOS bằng cách DOUBLE-CLICK file này trong Finder.
# (File .command double-click được; file .sh thì không.)
set -e
cd "$(dirname "$0")"

# Cài uv nếu chưa có (uv tự lo Python + thư viện, không cần cài Python thủ công).
if ! command -v uv >/dev/null 2>&1; then
  echo "Chưa có uv — đang cài đặt (một lần duy nhất)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

# Nhắc tạo .env nếu chưa có.
if [ ! -f .env ]; then
  echo ">> Chưa có file .env. Tạo từ mẫu..."
  cp .env.example .env
  echo ">> Hãy mở .env và dán GEMINI_API_KEY của bạn (lấy free tại https://aistudio.google.com)."
fi

echo ">> Khởi động app... (lần đầu uv sẽ tải thư viện, hơi lâu một chút)"
# --no-dev: chỉ cài thư viện chạy app, bỏ qua nhóm dev (pytest...) để nhẹ máy.
uv run --no-dev app.py
