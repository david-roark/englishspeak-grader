#!/usr/bin/env bash
# Đóng gói Speak Grader thành 1 file .zip để mang sang máy / hệ điều hành khác rồi triển khai.
# Gói gồm: mã nguồn (app.py, core/, tests/), script chạy (run.*), pyproject.toml + uv.lock,
#          .env.example, README, icon...
# KHÔNG gồm: .venv/, .env (bí mật), data/*.db, exports/*.xlsx, __pycache__/ ...  (theo .gitignore)
#
# Cách dùng (chạy trên máy dev Linux/macOS):
#   ./package.sh
# Máy đích chỉ cần giải nén rồi chạy run.bat (Windows) / run.command (macOS) / run.sh (Linux).
set -euo pipefail
cd "$(dirname "$0")"

APP_NAME="englishspeak-grader"

# Lấy version từ pyproject.toml (dòng dạng: version = "x.y.z")
VERSION="$(grep -m1 '^version' pyproject.toml | sed -E 's/.*"([^"]+)".*/\1/' || true)"
[ -z "${VERSION:-}" ] && VERSION="0.0.0"
STAMP="$(date +%Y%m%d_%H%M%S)"

OUT_DIR="dist"
mkdir -p "$OUT_DIR"
OUT_FILE="$OUT_DIR/${APP_NAME}-${VERSION}-${STAMP}.zip"

# Kiểm tra công cụ cần thiết.
if ! command -v git >/dev/null 2>&1; then
  echo "Loi: can 'git' de chon dung cac file nguon (ton trong .gitignore)." >&2
  exit 1
fi
if ! command -v zip >/dev/null 2>&1; then
  echo "Loi: can 'zip'. Cai dat: sudo apt install zip  (Debian/Ubuntu) hoac brew install zip (macOS)." >&2
  exit 1
fi

echo ">> Thu thap danh sach file (tracked + file moi chua ignore)..."
# --cached  : file da theo doi trong git
# --others  : file moi chua commit
# --exclude-standard : ton trong .gitignore/.git/info/exclude
# => phan anh DUNG working tree hien tai, tu dong loai .venv/ .env data/*.db exports/*.xlsx __pycache__ ...
mapfile -t FILES < <(git ls-files --cached --others --exclude-standard)

# Loc them mot so thu khong bao gio can trong goi trien khai.
FILTERED=()
for f in "${FILES[@]}"; do
  case "$f" in
    dist/*|*.zip) continue ;;   # chinh file dong goi
    .env)         continue ;;   # phong ho: khong bao gio dua bi mat vao goi
  esac
  FILTERED+=("$f")
done

if [ "${#FILTERED[@]}" -eq 0 ]; then
  echo "Loi: khong tim thay file nao de dong goi." >&2
  exit 1
fi

rm -f "$OUT_FILE"
printf '%s\n' "${FILTERED[@]}" | zip -q "$OUT_FILE" -@

ABS_OUT="$(cd "$(dirname "$OUT_FILE")" && pwd)/$(basename "$OUT_FILE")"
SIZE="$(du -h "$OUT_FILE" | cut -f1)"

echo ""
echo ">> Xong! Da tao goi trien khai:"
echo "   $ABS_OUT"
echo "   So file: ${#FILTERED[@]}   Dung luong: $SIZE"
echo ""
echo "Trien khai tren may khac:"
echo "  1. Chep file .zip sang may dich va giai nen."
echo "  2. Windows : double-click run.bat"
echo "     macOS   : double-click run.command"
echo "     Linux   : mo Terminal trong thu muc do roi chay  ./run.sh"
echo "  3. Lan dau app tu tao .env tu .env.example -> mo .env va dan GEMINI_API_KEY."
