from pathlib import Path
from src.chunking import ChunkingStrategyComparator

data_dir = Path("data/dang-ky-hoc-phan")
files = sorted(data_dir.glob("*.md"))[:3]

if not files:
    raise SystemExit("Không tìm thấy file .md trong data/dang-ky-hoc-phan")

comparator = ChunkingStrategyComparator()

for path in files:
    raw = path.read_text(encoding="utf-8")

    # Bỏ YAML frontmatter, chỉ giữ nội dung tài liệu.
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        content = parts[2].strip() if len(parts) == 3 else raw.strip()
    else:
        content = raw.strip()

    result = comparator.compare(content, chunk_size=700)

    print(f"\n=== {path.name} ===")
    for strategy, stats in result.items():
        print(
            f"{strategy:15} | "
            f"count = {stats['count']:3} | "
            f"avg_length = {stats['avg_length']:.1f}"
        )