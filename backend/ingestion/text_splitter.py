import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.core.config import settings


def get_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
        length_function=len,
    )


def split_documents(
    documents: list[str],
    metadatas: list[dict],
    ids: list[str],
) -> tuple[list[str], list[dict], list[str]]:
    """
    Split long documents into chunks. Short docs (< chunk_size) pass through unchanged.
    Updates chunk_index and doc_id metadata on each resulting chunk.
    """
    splitter = get_splitter()
    out_docs: list[str] = []
    out_metas: list[dict] = []
    out_ids: list[str] = []

    for doc, meta, doc_id in zip(documents, metadatas, ids):
        chunks = splitter.split_text(doc)
        for i, chunk in enumerate(chunks):
            chunk_meta = {**meta, "chunk_index": i, "doc_id": doc_id}
            chunk_id = hashlib.sha256(chunk.encode()).hexdigest()[:32]
            out_docs.append(chunk)
            out_metas.append(chunk_meta)
            out_ids.append(chunk_id)

    return out_docs, out_metas, out_ids
