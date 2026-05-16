from typing import List

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter


def split_document_text(content: str) -> List[str]:
    # RAG 不能把整篇文档直接塞给模型，必须先切成可召回的片段。
    # 这里优先按标题、段落、换行等自然边界切分，避免固定长度硬切导致语义割裂。
    text = (content or "").strip()
    if not text:
        return []

    splitter = RecursiveCharacterTextSplitter(
        # 900/150 是一期的保守配置：片段足够容纳流程说明，overlap 保留上下文衔接。
        chunk_size=900,
        chunk_overlap=150,
        separators=[
            "\n# ",
            "\n## ",
            "\n### ",
            "\n\n",
            "\n",
            "。", "；", "，",
            " ", "",
        ],
    )
    return [chunk.strip() for chunk in splitter.split_text(text) if chunk.strip()]
