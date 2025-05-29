import os
import torch.cuda
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from managers.config_manager import Config


def create_vector_store(config: Config, recreate=False):
    index_name = config.get_value("vector_store")
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-en-v1.5",
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    print(f"Looking for index {index_name}")
    print(os.path.abspath(index_name))
    if index_name is not None and os.path.exists(index_name) and not recreate:
        print("Vector store detected")
        db = FAISS.load_local(
            index_name, embeddings, allow_dangerous_deserialization=True
        )
        return db

    if recreate:
        print("Creating new index")
    else:
        print("Index couldn't be found")

    doc_path = config.get_value("documents_path")
    if doc_path is None:
        doc_path = input("Please provide path to the documents: ")

    loader = PyPDFDirectoryLoader(path=doc_path)

    text_splitter = SentenceTransformersTokenTextSplitter(
        model_name="BAAI/bge-large-en-v1.5", chunk_size=384, chunk_overlap=30
    )

    documents = loader.load_and_split(text_splitter)
    print("Loaded and split the documents")

    print(
        torch.cuda.get_device_name(0)
        if torch.cuda.is_available()
        else "No GPU detected"
    )

    db = FAISS.from_documents(documents, embeddings)
    db.save_local(index_name)
    print(f"Saved index: {index_name}")
    return db


if __name__ == "__main__":
    create_vector_store()
