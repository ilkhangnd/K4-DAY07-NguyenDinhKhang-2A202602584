# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** ActionPlan
**Thành viên:** 
- Nguyễn Đình Khang - 2A202602584
- Trần Long Khánh - 2A202602538
- Phạm Hồ Quang Dũng - 2A202602860 
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy định và lịch đăng ký học phần đại học

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn **quy định và lịch đăng ký học phần đại học** vì đây là nhu cầu gần gũi với sinh viên, có nhiều câu hỏi chứa mốc thời gian/điều kiện cần trả lời chính xác. Nguồn được lấy từ các trang công khai chính thức của UIT, UEH và FTU, tạo được corpus đa trường để kiểm tra metadata filter và khả năng truy vết.

### Danh sách tài liệu (Data Inventory)

| # | Tài liệu | Nguồn | Ngày lấy / phiên bản | Ký tự | Metadata chính |
|---|---|---|---|---:|---|
| 1 | Điều chỉnh thời gian đăng ký HK1 2026–2027 | UIT Portal | 2026-09-19 / not-stated | 1.111 | student, registration, vi |
| 2 | Quy định đăng ký và hủy học phần | UEH Đào tạo | 2026-09-19 / not-stated | 8.712 | student, registration, vi |
| 3 | Quy chế đào tạo theo tín chỉ | FTU QLĐT | 2026-09-19 / 2007-08-15 | 33.265 | all, registration, vi |
| 4 | TKB K65 và đăng ký tín chỉ bổ sung | FTU QLĐT | 2026-09-19 / not-stated | 1.244 | student, registration, vi |
| 5 | Đăng ký học phần thạc sĩ đợt 1/2026 | UEH Đào tạo | 2026-09-19 / not-stated | 12.819 | student, registration, vi |
| 6 | Điều chỉnh đăng ký học tập HK1 2026–2027 | FTU QLĐT | 2026-09-19 / not-stated | 3.792 | student, registration, vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [X] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [X] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `uit-dieu-chinh-...` | Xóa, truy vết và nhóm chunk theo tài liệu |
| `audience` | enum | `student`, `all` | Loại tài liệu không đúng đối tượng |
| `department` | string | `academic-affairs` | Thu hẹp theo đơn vị quản lý |
| `category` | string | `registration` | Thu hẹp theo nghiệp vụ |
| `source_url` | URL | trang UIT/UEH/FTU | Kiểm chứng câu trả lời |
| `retrieved_at` | date | `2026-09-19` | Theo dõi độ mới dữ liệu |
| `document_version` | string/date | `2007-08-15` | Phân biệt phiên bản quy định |
---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược | Số lượng chunk | Độ dài TB | Giữ ngữ cảnh? |
|---|---|---:|---:|---|
| `ftu-dieu-chinh-thoi-gian-dang-ky-hoc-tap.md` | FixedSizeChunker (`fixed_size`) | 30 | 689.1 | Trung bình |
|  | SentenceChunker (`by_sentences`) | 10 | 1919.6 | Có, nhưng chunk quá dài |
|  | RecursiveChunker (`recursive`) | 29 | 652.3 | Tốt |
| `ftu-quy-che-dao-tao-tin-chi.md` | FixedSizeChunker (`fixed_size`) | 76 | 692.4 | Trung bình |
|  | SentenceChunker (`by_sentences`) | 64 | 757.1 | Tốt |
|  | RecursiveChunker (`recursive`) | 81 | 597.0 | Tốt |
| `ftu-thoi-khoa-bieu-lich-dang-ky-tin-chi-k65.md` | FixedSizeChunker (`fixed_size`) | 26 | 695.3 | Trung bình |
|  | SenSentenceChunker (`by_sentences`)tence | 5 | 3361.0 | Có, nhưng chunk quá dài |
|  | RecursiveChunker (`recursive`) | 25 | 661.2 | Tốt |

> RecursiveChunker giữ ngữ cảnh tốt hơn vì ưu tiên tách theo đoạn văn, xuống dòng và câu, đồng thời vẫn giữ kích thước chunk gần ngưỡng 700 ký tự. FixedSizeChunker có độ dài ổn định nhưng có thể cắt giữa câu hoặc giữa quy định. SentenceChunker giữ nguyên câu nhưng có thể tạo chunk quá dài khi văn bản có ít dấu kết câu hoặc chứa nhiều menu/nhiễu.

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Đình Khang**
- **Loại chiến lược:** Custom — HeadingAwareChunker
- **Mô tả & lý do chọn cho chủ đề này:** Tôi chia tài liệu theo heading, Điều hoặc Mục vì quy định đăng ký học phần thường đã được tổ chức theo các phần ngữ nghĩa như thời gian đăng ký, điều kiện, giới hạn tín chỉ và điều chỉnh học phần. Nếu một mục quá dài, tôi dùng RecursiveChunker để chia nhỏ và gắn lại heading vào mọi mảnh con, giúp chunk luôn giữ ngữ cảnh.
- **Code snippet (nếu custom):**
```python
import re

from src.chunking import RecursiveChunker

class HeadingAwareChunker:
    """Tách theo heading hoặc Điều/Mục; section dài dùng recursive fallback."""

    HEADING_PATTERN = re.compile(
        r"^(#{1,6}\s+.+|(?:Điều|Mục)\s+\d+.*)$",
        re.MULTILINE | re.IGNORECASE,
    )

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        matches = list(self.HEADING_PATTERN.finditer(text))
        if not matches:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(text)

        chunks = []
        preamble = text[:matches[0].start()].strip()
        if preamble:
            chunks.extend(
                RecursiveChunker(chunk_size=self.chunk_size).chunk(preamble)
            )

        for index, match in enumerate(matches):
            heading = match.group().strip()
            section_end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(text)
            )
            body = text[match.end():section_end].strip()
            section = f"{heading}\n{body}".strip()

            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue

            available_size = max(1, self.chunk_size - len(heading) - 1)
            body_chunks = RecursiveChunker(chunk_size=available_size).chunk(body)

            for body_chunk in body_chunks:
                chunks.append(f"{heading}\n{body_chunk}".strip())

        return chunks
```

**Thành viên 2 — Trần Long Khánh**
- **Loại chiến lược:** RecursiveChunker, `chunk_size=500`.
- **Mô tả & lý do chọn:** Văn bản hành chính có điều, khoản và các dòng mốc thời gian, nên RecursiveChunker ưu tiên tách theo `\n\n`, `\n`, `. `, khoảng trắng rồi mới cắt ký tự. Cách này cố gắng giữ các ý trọn vẹn trước khi giảm kích thước chunk, phù hợp hơn với quy định có cấu trúc.
- **Code snippet (nếu custom):** Không áp dụng

**Thành viên 3 — Phạm Hồ Long Dũng**
- **Loại chiến lược:** FixedSizeChunker, `chunk_size=500`, `overlap=50`.
- **Mô tả & lý do chọn:** Chọn FixedSizeChunker có overlap làm baseline vì dễ kiểm soát độ dài chunk và overlap giảm nguy cơ cắt mất thông tin ngay tại ranh giới. Tuy nhiên, cách cắt theo ký tự không tôn trọng câu/điều khoản; kết quả benchmark với MockEmbedder chưa có evidence đáp án ở top-3, nên chủ yếu dùng để đối chiếu với Recursive và Heading-aware khi chạy embedding thật.
- **Code snippet (nếu custom):** Không áp dụng

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Đình Khang | HeadingAwareChunker, `chunk_size=700` | 7/10 (a) | Dùng embedding multilingual thật; evidence ở top-1 cho Q1–Q3, top-2 cho Q5. Việc giữ heading với section làm mốc thời gian còn đủ ngữ cảnh. | Bỏ lỡ chunk học phí UEH ở Q4; 209 chunks cho 6 trang cho thấy menu/nhiễu vẫn ảnh hưởng xếp hạng. |
| Phạm Hồ Long Dũng | FixedSizeChunker, `chunk_size=500`, `overlap=50` | 0/10 (a) | Độ dài chunk nhất quán; overlap hạn chế cắt mất thông tin ở ranh giới. | Không có đáp án gold xuất hiện trong preview top-3 ở cả 5 câu. Dùng MockEmbedder nên score không mang ngữ nghĩa và không công bằng khi đối chiếu trực tiếp với embedding thật. |
| Trần Long Khánh | RecursiveChunker, `chunk_size=500` | 3/10 (a) | Chạy lại chuẩn hoá với embedding multilingual thật có evidence ở Q1 và Q3 (top-2), Q5 (top-3); ưu tiên đoạn/dòng/câu phù hợp văn bản quy định. | Chưa lấy được evidence Q2, Q4; recursive không giữ heading nên các chunk chứa lịch dễ xếp sau phần tiêu đề/menu cùng trang. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Với bằng chứng có thể kiểm tra trực tiếp, HeadingAwareChunker hiện tốt nhất: đạt 7/10 retrieval-evidence và đưa mốc trả lời lên top-1 ở Q1–Q3. Khi chạy chuẩn hoá cùng bộ 5 query và embedding multilingual, Recursive đạt 3/10: vẫn lấy được Q1, Q3, Q5 nhưng ở hạng thấp hơn. FixedSize phù hợp làm baseline về độ dài/overlap, nhưng với MockEmbedder đạt 0/10 và chưa phản ánh chất lượng semantic retrieval.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Query | Gold answer | Chunk chứa thông tin |
|---|---|---|---|
| 1 | UIT khóa 20 đăng ký HK1 2026–2027 khi nào? | 23/08/2026, 09:00–16:00 | `uit-dieu-chinh...#0` |
| 2 | UEH hủy học phần đã đóng học phí và không rút học phí trước hạn nào? | Trước ngày thi kết thúc học phần 10 ngày | `ueh-quy-dinh...#12` |
| 3 | FTU K63/K64 đăng ký tín chỉ bổ sung khi nào? | 14/09–18/09/2026; mỗi ngày 09:00–22:00 | `ftu-thoi-khoa-bieu...#0` |
| 4 | Học phí học phần thạc sĩ cho sinh viên đại học UEH là bao nhiêu? | 1.650.000 VNĐ/tín chỉ | `ueh-dang-ky...#1` |
| 5 | FTU điều chỉnh lịch đăng ký cho khóa 60–64 thành thời gian nào? | 05/08–14/08/2026 | `ftu-dieu-chinh...#0` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | UIT khóa 20 đăng ký HK1 2026–2027 khi nào? | Heading-aware | Có — top-1 | Heading-aware: evidence top-1; Recursive: top-2; FixedSize: không có top-3. |
| 2 | UEH hủy học phần đã đóng học phí và không rút học phí trước hạn nào? | Heading-aware | Có — top-1 | Heading-aware lấy đúng `ueh-...#16`, chứa “trước ngày thi kết thúc ... 10 ngày”; Recursive và FixedSize không có evidence top-3 khi chạy chuẩn hoá. |
| 3 | FTU K63/K64 đăng ký tín chỉ bổ sung khi nào? | Heading-aware | Có — top-1 | Heading-aware: evidence top-1; Recursive: top-2; FixedSize: không có top-3. |
| 4 | Học phí học phần thạc sĩ cho sinh viên đại học UEH là bao nhiêu? | Chưa có chiến lược đạt | Không | Cả Heading-aware, Recursive và FixedSize đều không lấy được chunk chứa 1.650.000 VNĐ/tín chỉ trong top-3. |
| 5 | FTU điều chỉnh lịch đăng ký cho khóa 60–64 thành thời gian nào? | Heading-aware | Có — top-2 | Heading-aware lấy đúng `ftu-dieu-chinh-...#24` ở top-2; Recursive có evidence top-3; FixedSize không có evidence top-3. |

**Lưu ý về tính công bằng của so sánh:** Để chấm tự động, nhóm chạy lại đúng một corpus, 5 query, marker gold và `top_k=3`: Heading-aware và Recursive dùng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`; FixedSize giữ MockEmbedder như cấu hình gốc của thành viên. Các file `ket_qua_benchmark-*-auto.txt` lưu chunk ID và evidence extract. Vì chưa có output agent/LLM, đây là điểm retrieval-evidence, chưa phải điểm rubric cuối cùng.

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Ở Q1, top-3 của lượt không filter và lượt `{"audience": "student"}` giống hệt nhau, nên filter hiện chưa làm kết quả tốt hơn. Nguyên nhân là corpus có phần lớn tài liệu cho `student` và chưa có tài liệu `staff` cùng chủ đề để tạo cạnh tranh thực sự. Nếu làm lại, nhóm sẽ bổ sung tài liệu staff công khai và dùng một câu hỏi mơ hồ về đối tượng để đo được đánh đổi precision/recall của filter.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - Tách theo heading đưa các mốc thời gian/quy định quan trọng lên top-1 ở Q1–Q3, tốt hơn FixedSize và Recursive trong lần đo chuẩn hoá.
> - Chỉ đúng `doc_id` chưa đủ: Q4 trả về đúng tài liệu UEH nhưng không có chunk nào trong top-3 chứa mức học phí; vì vậy nhóm chấm theo evidence ở cấp nội dung chunk.
> - Embedding backend ảnh hưởng mạnh đến retrieval: FixedSize với MockEmbedder đạt 0/10, trong khi embedding multilingual cho phép phân biệt câu hỏi và section liên quan tốt hơn.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một corpus, chiến lược chunking quyết định thông tin nào được giữ chung với tiêu đề và được đưa vào ngữ cảnh truy xuất. Heading-aware phù hợp nhất với văn bản quy định vì không cắt rời điều/mục; Recursive vẫn lấy được một số evidence nhưng thường ở hạng thấp hơn. FixedSize hữu ích như baseline đơn giản, nhưng cần embedding có ngữ nghĩa và dữ liệu sạch để đánh giá công bằng.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ làm sạch menu, footer và danh sách liên kết lặp lại trước khi chunk để giảm 209 chunks nhiễu từ 6 tài liệu. Đồng thời, nhóm sẽ bổ sung tài liệu công khai cho audience `staff` và thiết kế lại câu A/B để metadata filter thực sự thay đổi kết quả. Cuối cùng, mọi thành viên sẽ chạy cùng embedding backend, cùng 5 query và lưu evidence extract để việc so sánh tái lập được.
---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 8 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 6 / 10 |
| Thuyết trình (Demo) | 0 / 5 |
| **Tổng phần nhóm** | ** 27 / 40** |
