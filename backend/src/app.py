import os
import torch.cuda
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from backend.src.config_manager import ConfigManager


def create_vector_store(recreate=False):
    config = ConfigManager("config.yaml")
    index_name = config["VECTOR_STORE"]

    if os.path.exists(index_name) and not recreate:
        print("Vector store detected")
        db = FAISS.load_local(index_name)
        return db

    if "DOCUMENTS_PATH" not in config:
        config["DOCUMENTS_PATH"] = input("Please provide path to the documents: ")

    loader = PyPDFDirectoryLoader(dir=config["DOCUMENTS_PATH"])

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
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-en-v1.5",
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    db = FAISS.from_documents(documents, embeddings)
    db.save_local(index_name)
    print(f"Saved index: {index_name}")
    return db


if __name__ == "__main__":
    create_vector_store()
