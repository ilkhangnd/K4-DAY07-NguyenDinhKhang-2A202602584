"""Compare retrieval results for the course-registration corpus.

Run with:
    python bench.py
    python bench.py --data-dir data/dang-ky-hoc-phan
"""

from __future__ import annotations

import argparse
import contextlib
import os
import re
from pathlib import Path

from src.chunking import FixedSizeChunker, RecursiveChunker
from src.embeddings import LOCAL_EMBEDDING_MODEL, LocalEmbedder, MockEmbedder
from src.models import Document
from src.store import EmbeddingStore


class HeadingAwareChunker:
    """Split regulations by heading, then recursively split long sections."""

    HEADING_PATTERN = re.compile(
        r"^(#{1,6}\s+.+|(?:Điều|Mục)\s+\d+.*)$",
        re.MULTILINE | re.IGNORECASE,
    )

    def __init__(self, chunk_size: int = 700) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        matches = list(self.HEADING_PATTERN.finditer(text))
        if not matches:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(text)

        chunks: list[str] = []
        preamble = text[: matches[0].start()].strip()
        if preamble:
            chunks.extend(RecursiveChunker(chunk_size=self.chunk_size).chunk(preamble))

        for index, match in enumerate(matches):
            heading = match.group().strip()
            section_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            body = text[match.end() : section_end].strip()
            section = f"{heading}\n{body}".strip()

            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue

            body_size = max(1, self.chunk_size - len(heading) - 1)
            for body_chunk in RecursiveChunker(chunk_size=body_size).chunk(body):
                chunks.append(f"{heading}\n{body_chunk}".strip())

        return chunks


BENCHMARK_QUERIES = [
    {
        "question": "UIT khóa 20 đăng ký HK1 2026-2027 khi nào?",
        "metadata_filter": {"audience": "student"},
        "expected_doc_id": "uit-dieu-chinh-thoi-gian-dang-ky-hoc-phan",
        "answer_marker": "Ngày 23/08/2026 (09h00–16h00)",
    },
    {
        "question": "UEH hủy học phần đã đóng học phí và không rút học phí trước hạn nào?",
        "metadata_filter": None,
        "expected_doc_id": "ueh-quy-dinh-dang-ky-huy-hoc-phan",
        "answer_marker": "trước ngày thi kết thúc học phần của học phần hủy 10 ngày",
    },
    {
        "question": "FTU K63/K64 đăng ký tín chỉ bổ sung khi nào?",
        "metadata_filter": None,
        "expected_doc_id": "ftu-thoi-khoa-bieu-lich-dang-ky-tin-chi-k65",
        "answer_marker": "đăng ký từ ngày 14/9/2026 đến ngày 18/9/2026",
    },
    {
        "question": "Học phí học phần thạc sĩ cho sinh viên đại học UEH là bao nhiêu?",
        "metadata_filter": None,
        "expected_doc_id": "ueh-dang-ky-hoc-phan-thac-si-dot1-2026",
        "answer_marker": "Mức học phí: 1.650.000 VNĐ/tín chỉ",
    },
    {
        "question": "FTU điều chỉnh lịch đăng ký cho khóa 60-64 thành thời gian nào?",
        "metadata_filter": None,
        "expected_doc_id": "ftu-dieu-chinh-thoi-gian-dang-ky-hoc-tap",
        "answer_marker": "Thời gian đăng ký mới sau điều chỉnh: từ ngày 05/8/2026 đến ngày 14/8/2026",
    },
]


def read_markdown(path: Path) -> tuple[dict[str, str], str]:
    """Return simple YAML frontmatter and the Markdown body for one file."""
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return {}, raw.strip()

    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw.strip()

    metadata: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, parts[2].strip()


def make_chunker(strategy: str, chunk_size: int, overlap: int):
    """Create one comparable chunker; only this choice changes per member."""
    if strategy == "fixed":
        return FixedSizeChunker(chunk_size=chunk_size, overlap=overlap)
    if strategy == "recursive":
        return RecursiveChunker(chunk_size=chunk_size)
    return HeadingAwareChunker(chunk_size=chunk_size)


def load_chunk_documents(
    data_dir: Path, chunk_size: int, strategy: str, overlap: int
) -> list[Document]:
    chunker = make_chunker(strategy, chunk_size, overlap)

    documents: list[Document] = []
    for path in sorted(data_dir.glob("*.md")):
        frontmatter, content = read_markdown(path)
        for index, chunk in enumerate(chunker.chunk(content)):
            metadata = {
                **frontmatter,
                "doc_id": path.stem,
                "chunk_index": str(index),
            }
            documents.append(
                Document(
                    id=f"{path.stem}#{index}",
                    content=chunk,
                    metadata=metadata,
                )
            )
    return documents


def evidence_rank(results: list[dict], benchmark: dict) -> int | None:
    """Return the rank whose chunk has both the gold source and answer evidence."""
    for rank, result in enumerate(results, start=1):
        is_gold_doc = result["metadata"].get("doc_id") == benchmark["expected_doc_id"]
        if is_gold_doc and benchmark["answer_marker"].casefold() in result["content"].casefold():
            return rank
    return None


def print_search_case(label: str, results: list[dict], benchmark: dict) -> int:
    """Print top-3 and return a provisional 0/1/2 retrieval-evidence score."""
    print(f"  {label}")
    if not results:
        print("    Không có kết quả phù hợp.")
        return 0

    for rank, result in enumerate(results, start=1):
        preview = " ".join(result["content"].split())[:240]
        has_marker = benchmark["answer_marker"].casefold() in result["content"].casefold()
        is_gold_doc = result["metadata"].get("doc_id") == benchmark["expected_doc_id"]
        evidence = "YES" if has_marker and is_gold_doc else "NO"
        print(
            f"    {rank}. score={result['score']:.3f} "
            f"chunk_id={result['id']} "
            f"doc_id={result['metadata'].get('doc_id')} evidence={evidence}"
        )
        print(f"       {preview}")
        if has_marker and is_gold_doc:
            content_folded = result["content"].casefold()
            start = max(0, content_folded.find(benchmark["answer_marker"].casefold()) - 80)
            end = start + len(benchmark["answer_marker"]) + 180
            excerpt = " ".join(result["content"][start:end].split())
            print(f"       Evidence extract: {excerpt}")

    rank = evidence_rank(results, benchmark)
    if rank == 1:
        print("    Kết quả evidence: 2/2 (chunk đúng có đáp án ở top-1).")
        return 2
    if rank is not None:
        print(f"    Kết quả evidence: 1/2 (chunk đúng có đáp án ở top-{rank}).")
        return 1
    print("    Kết quả evidence: 0/2 (top-3 không chứa đáp án gold).")
    return 0


def make_embedder(embedding: str):
    if embedding == "mock":
        return MockEmbedder()
    # The model is downloaded once during setup.  Offline mode prevents repeated
    # network metadata checks every time the benchmark is run.
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    return LocalEmbedder(model_name=LOCAL_EMBEDDING_MODEL)


def run_benchmark(
    data_dir: Path, chunk_size: int, embedding: str, strategy: str, overlap: int
) -> None:
    documents = load_chunk_documents(data_dir, chunk_size, strategy, overlap)
    if not documents:
        print(f"Không tìm thấy chunk nào trong: {data_dir}")
        return

    embedder = make_embedder(embedding)
    store = EmbeddingStore(
        collection_name="course_registration_benchmark", embedding_fn=embedder
    )
    store.add_documents(documents)
    print("=== CHECKPOINT 6: RETRIEVAL BENCHMARK ===")
    strategy_name = {
        "heading": "HeadingAwareChunker",
        "fixed": "FixedSizeChunker",
        "recursive": "RecursiveChunker",
    }[strategy]
    detail = f", overlap={overlap}" if strategy == "fixed" else ""
    print(f"Chiến lược chunking: {strategy_name} (chunk_size={chunk_size}{detail})")
    print(f"Embedding backend: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")
    print(f"Đã nạp {len(documents)} chunks từ {len(list(data_dir.glob('*.md')))} tài liệu.\n")

    total_score = 0
    for number, benchmark in enumerate(BENCHMARK_QUERIES, start=1):
        query = benchmark["question"]
        metadata_filter = benchmark["metadata_filter"]

        print(f"Q{number}: {query}")
        print(f"Gold evidence: {benchmark['answer_marker']}")

        if metadata_filter:
            unfiltered = store.search(query, top_k=3)
            print_search_case("A. Không filter:", unfiltered, benchmark)
            filtered = store.search_with_filter(query, top_k=3, metadata_filter=metadata_filter)
            total_score += print_search_case(
                f"B. Có filter {metadata_filter}:", filtered, benchmark
            )
        else:
            results = store.search(query, top_k=3)
            total_score += print_search_case("Top-3 (không filter):", results, benchmark)
        print()

    print(f"Tổng điểm retrieval-evidence tạm thời: {total_score}/10")
    print(
        "Lưu ý: đây chỉ chấm chunk có chứa đáp án. "
        "Điểm 2/2 chính thức còn cần kiểm tra câu trả lời của agent/LLM dựa trên context đó."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark course-registration retrieval.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/dang-ky-hoc-phan"))
    parser.add_argument("--chunk-size", type=int, default=700)
    parser.add_argument(
        "--strategy", choices=("heading", "fixed", "recursive"), default="heading",
        help="Choose the member's chunking strategy.",
    )
    parser.add_argument(
        "--overlap", type=int, default=50,
        help="Overlap used only by --strategy fixed.",
    )
    parser.add_argument(
        "--embedding", choices=("local", "mock"), default="local",
        help="local uses the multilingual semantic model; mock is only for comparison.",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("ket_qua_benchmark.txt"),
        help="Text file that receives the same benchmark output.",
    )
    args = parser.parse_args()
    with args.output.open("w", encoding="utf-8") as output_file:
        with contextlib.redirect_stdout(output_file):
            run_benchmark(
                args.data_dir,
                args.chunk_size,
                args.embedding,
                args.strategy,
                args.overlap,
            )

    print(f"Đã ghi kết quả vào {args.output}")
    print(args.output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
