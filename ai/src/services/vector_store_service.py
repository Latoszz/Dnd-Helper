import os
from collections import Counter
from langchain.vectorstores import VectorStore
from langchain_core.vectorstores.base import BaseRetriever
from langchain_postgres.vectorstores import PGVector
from langchain.indexes import index
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain.indexes import SQLRecordManager
from managers.config_manager import Config
from langchain_community.document_loaders.pdf import PyPDFDirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class VectorStoreService:

    __batch_size = 500

    def __init__(self, config: Config, to_reembed=False):
        self.config = config
        connection = config.get_value("vector_store")["conn_str"]
        if connection == "no_free_database":
            connection = os.getenv("POSTGRES_TEG")
        collection_name = config.get_value("vector_store")["collection_name"]
        embeddings = GoogleGenerativeAIEmbeddings(model=config.get_value("model_name"))
        # environment must have GOOGLE_API_KEY variable or pass it throgh kwargs

        self._vector_store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=connection,
            use_jsonb=True,
            create_extension=True,
        )
        self.record_manager = SQLRecordManager(
            db_url=connection, namespace=config.get_value("vector_store")["namespace"]
        )
        self.record_manager.create_schema()
        if to_reembed:
            self.add_to_vector_store()

    def add_to_vector_store(self, path=None):
        if path is None:
            doc_path = self.config.get_value("documents_path")
        else:
            doc_path = path

        if doc_path is None:
            return

        if os.path.isdir(doc_path):
            loader = PyPDFDirectoryLoader(path=doc_path)
        else:
            loader = PyPDFLoader(file_path=doc_path)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=[
                "\n\n",
                "\n",
                " ",
                ".",
                ",",
                "\u200b",  # Zero-width space
                "\uff0c",  # Fullwidth comma
                "\u3001",  # Ideographic comma
                "\uff0e",  # Fullwidth full stop
                "\u3002",  # Ideographic full stop
                "",
            ],
        )
        splitted_docs = loader.load_and_split(splitter)
        result = {}
        length = len(splitted_docs)
        print(length)
        # input("A: ")
        # if length > VectorStoreService.__batch_size:
        #     vector_chunks = [
        #         splitted_docs[i : i + VectorStoreService.__batch_size]
        #         for i in range(0, len(splitted_docs), VectorStoreService.__batch_size)
        #     ]
        #     for chunk in vector_chunks:
        #         print(chunk)
        #         result = Counter(result) + Counter(
        #             index(
        #                 docs_source=chunk,
        #                 record_manager=self.record_manager,
        #                 cleanup="incremental",
        #                 source_id_key="source",
        #                 vector_store=self.vector_store,
        #                 batch_size=VectorStoreService.__batch_size,
        #             )
        #         )
        # else:
        result = index(
            docs_source=splitted_docs,
            record_manager=self.record_manager,
            cleanup="incremental",
            source_id_key="source",
            vector_store=self.vector_store,
            batch_size=VectorStoreService.__batch_size,
        )
        return result

    @property
    def vector_store(self) -> VectorStore:
        return self._vector_store

    def as_retriever(self, **kwargs) -> BaseRetriever:
        return self.vector_store.as_retriever(kwargs=kwargs)
