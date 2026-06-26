import os
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


load_dotenv()


def get_rag_answer(question):
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError("Chưa có GOOGLE_API_KEY trong file .env")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )

    vector_db = Chroma(
        persist_directory="vector_db",
        embedding_function=embeddings
    )

    retriever = vector_db.as_retriever(
        search_kwargs={"k": 4}
    )

    docs = retriever.invoke(question)

    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = ChatPromptTemplate.from_template("""
Bạn là chatbot hỗ trợ tham khảo thông tin y tế.

Quy tắc trả lời:
- Chỉ trả lời dựa trên ngữ cảnh tài liệu được cung cấp.
- Không tự ý chẩn đoán bệnh.
- Không thay thế bác sĩ.
- Nếu tài liệu chưa cung cấp đủ thông tin, hãy nói rõ là chưa đủ thông tin.
- Trả lời bằng tiếng Việt, dễ hiểu, ngắn gọn.

Ngữ cảnh tài liệu:
{context}

Câu hỏi của người dùng:
{question}

Câu trả lời:
""")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        google_api_key=api_key
    )

    chain = prompt | llm

    response = chain.invoke({
        "context": context,
        "question": question
    })

    return response.content, docs


if __name__ == "__main__":
    question = "Cholesterol cao có nguy hiểm không?"
    answer, docs = get_rag_answer(question)

    print("===== CÂU HỎI =====")
    print(question)

    print("\n===== CÂU TRẢ LỜI =====")
    print(answer)

    print("\n===== TÀI LIỆU ĐƯỢC TRUY XUẤT =====")
    for i, doc in enumerate(docs, start=1):
        print(f"\n--- Nguồn {i} ---")
        print(doc.page_content[:500])