import os
import torch.cuda
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from config.config_manager import get_config

print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU detected")

config = get_config()

if "DOCUMENTS_PATH" not in config:
    config["DOCUMENTS_PATH"] = input("Please provide path to the documents: ")

loader = PyPDFDirectoryLoader(dir=config["DOCUMENTS_PATH"])

text_splitter = SentenceTransformersTokenTextSplitter(
    model_name="BAAI/bge-large-en-v1.5", chunk_size=384, chunk_overlap=30
)

documents = loader.load_and_split(text_splitter)
print("Loaded and split the documents")

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-en-v1.5",
    model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

db = FAISS.from_documents(documents, embeddings)
db.save_local( os.path.join(config["VECTOR_STORE_PATH"], config["FAISS_INDEX_NAME"]))
print(f"Saved index in {config["VECTOR_STORE_PATH"]}")
