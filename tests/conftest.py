"""Cho pytest thấy `src/` mà không cần cài gói.

Trước đây mỗi file test tự chèn `src` vào `sys.path`. File test thứ tư quên làm
việc đó và cả bộ test **không thu thập nổi** (`ModuleNotFoundError`). Gom về một
chỗ để lần sau thêm file test là chạy được ngay.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
