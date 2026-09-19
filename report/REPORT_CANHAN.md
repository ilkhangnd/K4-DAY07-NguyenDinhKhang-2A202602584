# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đình Khang
**Nhóm:** Nhóm chủ đề Đăng ký học phần
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Cosine similarity cao nghĩa là hai embedding có hướng gần nhau; với text embedding, điều này cho thấy nội dung/ngữ nghĩa của hai câu gần nhau. Điểm gần 1 biểu thị tương đồng mạnh, gần 0 biểu thị ít liên quan và gần -1 biểu thị hướng đối lập.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên cần đăng ký học phần trước hạn.
- Câu B: Người học phải ghi danh môn học đúng thời gian quy định.
- Tại sao tương đồng: Hai câu dùng từ khác nhau nhưng đều yêu cầu sinh viên đăng ký môn học trước thời hạn, nên thể hiện cùng một ý nghĩa.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Thư viện cho phép gia hạn sách trực tuyến.
- Câu B: Ký túc xá thông báo lịch bảo trì thang máy.
- Tại sao khác: Hai câu nói về hai dịch vụ đại học khác nhau và không chia sẻ mục đích hay quy trình.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine so sánh hướng của vector nên tập trung vào mức độ giống về ngữ nghĩa và ít bị ảnh hưởng bởi độ lớn vector hoặc độ dài câu. Với vector đã chuẩn hoá trong store, dot product bằng cosine, giúp tìm kiếm gọn và ổn định hơn khoảng cách Euclid.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11...) = 23`.
>
> Đối chiếu bằng `FixedSizeChunker(chunk_size=500, overlap=50).chunk('a' * 10000)` cũng trả về **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> `ceil((10000 - 100) / (500 - 100)) = ceil(24.75) = 25`, nên số chunk tăng từ 23 lên 25; kết quả được kiểm lại bằng `FixedSizeChunker` là 25. Overlap lớn giữ lại ngữ cảnh ở ranh giới hai chunk, giảm nguy cơ cắt đôi điều kiện hoặc mốc thời gian, đổi lại tăng số vector, thời gian và chi phí embedding.

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
$ pytest tests/ -v
============================== 42 passed in 0.03s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | cao / thấp | | |
| 2 | | | cao / thấp | | |
| 3 | | | cao / thấp | | |
| 4 | | | cao / thấp | | |
| 5 | | | cao / thấp | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
