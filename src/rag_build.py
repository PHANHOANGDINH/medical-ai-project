import os
from dotenv import load_dotenv

from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings


load_dotenv()


def load_documents():
    documents = []

    pdf_loader = PyPDFDirectoryLoader("data/documents")
    pdf_docs = pdf_loader.load()
    documents.extend(pdf_docs)

    txt_loader = DirectoryLoader(
        "data/documents",
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    txt_docs = txt_loader.load()
    documents.extend(txt_docs)

    return documents


def build_vector_db():
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError("Chưa có GOOGLE_API_KEY trong file .env")

    documents = load_documents()

    if len(documents) == 0:
        raise ValueError("Chưa có tài liệu trong thư mục data/documents")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(documents)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="vector_db"
    )

    print("Đã tạo vector database thành công.")
    print("Số tài liệu gốc:", len(documents))
    print("Số đoạn sau khi chia nhỏ:", len(chunks))


if __name__ == "__main__":
    build_vector_db()