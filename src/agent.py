from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin liên quan trong cơ sở tri thức."

        context_parts = []
        for index, result in enumerate(results, start=1):
            metadata = result["metadata"]
            source = metadata.get(
                "source_url",
                metadata.get("source", metadata.get("doc_id", result["id"])),
            )
            context_parts.append(f"[{index}] Nguồn: {source}\n{result['content']}")

        context = "\n\n".join(context_parts)
        prompt = f"""Chỉ trả lời dựa trên ngữ cảnh bên dưới.
Nếu ngữ cảnh không đủ, hãy nói rõ không tìm thấy thông tin.
Khi dùng thông tin, trích dẫn số nguồn như [1], [2].

Ngữ cảnh:
{context}

Câu hỏi: {question}
Trả lời:"""
        return self.llm_fn(prompt)
