import os
import json
from pathlib import Path

from dotenv import load_dotenv

from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


load_dotenv()


DOCUMENT_FOLDER = "data/documents"
VECTOR_DB_FOLDER = "vector_db"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150

LOCAL_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_jsonl_documents(folder_path=DOCUMENT_FOLDER):
    documents = []
    jsonl_files = list(Path(folder_path).rglob("*.jsonl"))

    for file_path in jsonl_files:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    print(f"Bỏ qua dòng JSONL lỗi: {file_path} - dòng {line_number}")
                    continue

                content = (
                    item.get("content")
                    or item.get("text")
                    or item.get("page_content")
                    or ""
                )

                if not content.strip():
                    continue

                metadata = {
                    "file_name": file_path.name,
                    "line_number": line_number,
                    "title": item.get("title", ""),
                    "source": item.get("source", ""),
                    "category": item.get("category", "")
                }

                documents.append(
                    Document(
                        page_content=content,
                        metadata=metadata
                    )
                )

    return documents


def load_documents():
    documents = []

    print("Đang đọc tài liệu PDF...")
    pdf_loader = PyPDFDirectoryLoader(DOCUMENT_FOLDER)
    pdf_docs = pdf_loader.load()
    documents.extend(pdf_docs)

    print("Đang đọc tài liệu TXT...")
    txt_loader = DirectoryLoader(
        DOCUMENT_FOLDER,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    txt_docs = txt_loader.load()
    documents.extend(txt_docs)

    print("Đang đọc tài liệu JSONL...")
    jsonl_docs = load_jsonl_documents(DOCUMENT_FOLDER)
    documents.extend(jsonl_docs)

    return documents


def build_vector_db():
    documents = load_documents()

    if len(documents) == 0:
        raise ValueError("Chưa có tài liệu trong thư mục data/documents")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = splitter.split_documents(documents)

    print("=" * 60)
    print("Số tài liệu gốc:", len(documents))
    print("Số đoạn sau khi chia nhỏ:", len(chunks))
    print("Đang dùng embedding local:", LOCAL_EMBEDDING_MODEL)
    print("=" * 60)

    embeddings = HuggingFaceEmbeddings(
        model_name=LOCAL_EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_FOLDER
    )

    print("=" * 60)
    print("Đã tạo vector database thành công bằng embedding local.")
    print("Thư mục lưu:", VECTOR_DB_FOLDER)
    print("=" * 60)


if __name__ == "__main__":
    build_vector_db()