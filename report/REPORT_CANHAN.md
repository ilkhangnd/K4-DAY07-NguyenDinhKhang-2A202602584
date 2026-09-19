# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đình Khang
**Nhóm:** ActionPlan
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (High cosine similarity) nghĩa là góc tạo bởi hai vector rất nhỏ, cho thấy hai đối tượng được biểu diễn dưới dạng số liệu hoặc văn bản có hướng gần như trùng khớp và nội dung/ý nghĩa rất giống nhau. Nói cách khác, hai embedding hướng gần nhau; điểm càng gần 1 càng tương đồng. 

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên cần đăng ký môn học trước hạn"
- Câu B: "Người học phải ghi danh học phần đúng thời gian quy định"
- Tại sao tương đồng: Hai câu dùng từ khác nhau nhưng đều yêu cầu sinh viên đăng ký môn học trước thời hạn, nên thể hiện cùng một ý nghĩa.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Thư viện gia hạn sách trực tuyến"
- Câu B: "Học phí được thanh toán theo từng học kỳ"
- Tại sao khác: Hai câu đề cập đến hai vấn đề khác nhau, không có sự tương đồng hoặc gần giống nhau. 

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Độ tương tự cosine (cosine similarity) được ưu tiên hơn và phù hợp hơn khoảng cách Euclid (Euclidean distance) vì nó đo độ giống về hướng/ngữ nghĩa của vector, ít bị ảnh hưởng bởi độ lớn hay độ dài của văn bản

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> ceil((10000 - 50) / (500 - 50))
> = ceil(9950 / 450)
> = ceil(22.11...)
> = 23 chunks
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> ceil((10000 - 100) / (500 - 100))
> = ceil(9900 / 400)
> = ceil(24.75)
> = 25 chunks
> Số lượng chunk tăng từ 23 lên 25 khi overlap tăng từ 50 lên 100. Overlap lớn hơn giữ lại nhiều ngữ cảnh ở vùng giao giữa hai chunk, nên giảm nguy cơ một điều kiện, mốc thời gian hoặc câu trả lời bị cắt đôi. Tuy nhiên, cách này tạo thêm chunk, làm tăng chi phí embedding, dung lượng lưu trữ và thời gian truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])\s+` để tách tại vị trí sau dấu kết thúc câu; lookbehind giữ lại dấu câu trong chunk thay vì làm câu bị cụt. Text rỗng trả về `[]`, các câu được `strip()` rồi gom theo `max_sentences_per_chunk`. Edge case chưa xử lý hoàn toàn là chữ viết tắt như `TS.`, `v.v.` và số thập phân có thể bị hiểu nhầm là điểm kết thúc câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử separator theo thứ tự `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng là chuỗi rỗng; mảnh nào còn dài sẽ được tách đệ quy bằng separator nhỏ hơn. Sau đó tôi gom các mảnh nhỏ liền kề lại đến gần `chunk_size` để tránh tạo nhiều chunk vụn. Base case là text rỗng, text đã đủ ngắn, hoặc không còn separator — khi đó fallback sang cắt theo ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` biến từng `Document` thành record in-memory gồm `id`, `content`, bản sao `metadata` và embedding; `doc_id` được bổ sung nếu metadata chưa có. `search` embedding câu hỏi, tính dot product với embedding các record, sắp xếp score giảm dần rồi trả tối đa `top_k` kết quả. Vì embedding được chuẩn hoá, dot product chính là cosine similarity.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc candidate theo metadata **trước** khi tính similarity, tránh trường hợp top-k bị chiếm bởi tài liệu sai audience rồi không còn kết quả hợp lệ. `delete_document` lọc bỏ mọi record có `metadata['doc_id']` khớp với file gốc, vì một file có thể sinh nhiều chunk `file#0`, `file#1`; hàm trả `True` nếu đã xoá ít nhất một record.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent truy xuất top-k trước, sau đó ghép context theo thứ tự `[1]`, `[2]`, `[3]`, kèm URL nguồn của từng chunk để truy vết được. Prompt yêu cầu LLM chỉ dùng context, nói rõ khi không có đủ thông tin và trích dẫn số nguồn khi trả lời. Nếu store rỗng, hàm trả thông báo không tìm thấy thay vì gọi LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
(.venv) nguyendinhkhang@wekipedkane K4A-DAY07-NguyenDinhKhang-2A202602584 % pytest tests/ -v                                                               
======================================================================== test session starts =========================================================================
platform darwin -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0 -- /Users/nguyendinhkhang/AITHUCCHIEN/K4A-DAY07-NguyenDinhKhang-2A202602584/.venv/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/nguyendinhkhang/AITHUCCHIEN/K4A-DAY07-NguyenDinhKhang-2A202602584
plugins: anyio-4.15.1
collected 42 items                                                                                                                                                   

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                                          [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                                   [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                                            [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                                             [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                                  [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                                  [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                                        [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                                         [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                                       [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                                         [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                                         [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                                    [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                                [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                                          [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                                 [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                                     [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                                               [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                                     [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                                         [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                                           [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                                             [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                                   [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                                        [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                                          [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                                              [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                                           [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                                    [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                                   [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                                              [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                                          [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                                     [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                                         [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                                               [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                                         [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                                      [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                                    [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                                   [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                                       [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                                  [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                                           [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                                 [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                                                     [100%]

========================================================================= 42 passed in 0.07s =========================================================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên cần đăng ký học phần trước hạn. | Người học phải ghi danh môn học đúng thời gian quy định. | Cao | 0.654 | Đúng |
| 2 | Thư viện cho phép gia hạn sách trực tuyến. | Ký túc xá thông báo lịch bảo trì thang máy. | Thấp | 0.155 | Đúng |
| 3 | Hủy học phần đã đóng học phí cần thực hiện đúng thời hạn. | Sinh viên có thể rút học phí nếu hủy môn trước hạn. | Trung bình | 0.390 | Đúng |
| 4 | Lịch đăng ký tín chỉ bổ sung dành cho khóa K63 và K64. | Thời khóa biểu chính thức được công bố cho sinh viên K65. | Cao | 0.589 | Đúng |
| 5 | Mức học phí là 1.650.000 đồng mỗi tín chỉ. | Lệ phí làm lại thẻ sinh viên được thanh toán tại phòng công tác sinh viên. | Trung bình | 0.401 | Đúng |


**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 5 có điểm 0.401 dù hai khoản tiền hoàn toàn khác nhau; embedding vẫn nhận ra chúng cùng thuộc ngữ cảnh thanh toán trong trường đại học. Ngược lại, cặp 3 chỉ đạt 0.390 dù đều nói về hủy học phần/học phí, vì một câu nhấn vào thời hạn còn câu kia nhấn vào điều kiện rút tiền. Điều này cho thấy embedding nắm ngữ nghĩa ở mức khái quát, nhưng không tự bảo đảm lấy đúng điều kiện hoặc số liệu chi tiết.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | UIT khóa 20 đăng ký HK1 2026–2027 khi nào? | `uit-...#2`: lịch của khóa 20, 23/08/2026, 09h00–16h00. | 0.830 | Có, top-1 | Từ context: khóa 20 đăng ký ngày 23/08/2026, 09h00–16h00. |
| 2 | UEH hủy học phần đã đóng học phí và không rút học phí trước hạn nào? | `ueh-quy-dinh-...#16`: hủy đã đóng học phí, không rút phí. | 0.723 | Có, top-1 | Từ context: trước ngày thi kết thúc của học phần hủy 10 ngày. |
| 3 | FTU K63/K64 đăng ký tín chỉ bổ sung khi nào? | `ftu-thoi-khoa-bieu-...#23`: lịch K63/K64. | 0.615 | Có, top-1 | Từ context: 14/09–18/09/2026; mỗi ngày 09h00–22h00. |
| 4 | Học phí học phần thạc sĩ cho sinh viên đại học UEH là bao nhiêu? | `ueh-dang-ky-...#2`: phần giới thiệu/đối tượng UEH, không có mức học phí. | 0.653 | Không; top-3 không chứa mức phí | Không đủ context để trả lời an toàn; gold là 1.650.000 VNĐ/tín chỉ nhưng chunk đúng không vào top-3. |
| 5 | FTU điều chỉnh lịch đăng ký cho khóa 60–64 thành thời gian nào? | `ftu-thoi-khoa-bieu-...#23`: lịch K63/K64, không đúng câu hỏi. Chunk đúng `ftu-dieu-chinh-...#24` ở top-2. | 0.781 | Có, top-2 | Từ context top-2: thời gian mới là 05/08–14/08/2026. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Em học được rằng cần tách phần chunking ra ngoài `EmbeddingStore`: một file phải tạo nhiều `Document` với `id` theo dạng `file#i`, còn `metadata['doc_id']` vẫn trỏ về file gốc. RecursiveChunker của Khánh cũng cho thấy tách theo ranh giới văn bản tốt hơn cắt cứng, nhưng với quy định có heading rõ ràng thì lặp lại heading trong mỗi chunk giúp retrieval ổn định hơn. So sánh với FixedSize dùng MockEmbedder cho thấy chọn embedding backend ảnh hưởng lớn đến kết quả benchmark.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |