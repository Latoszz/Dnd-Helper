import os
import tempfile
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import create_async_engine
from langchain.vectorstores import VectorStore
from langchain_core.vectorstores.base import BaseRetriever
from langchain_core.documents.base import Document
from langchain_postgres.vectorstores import PGVector
from langchain.indexes import aindex
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain.indexes import SQLRecordManager
from langchain_community.document_loaders.pdf import PyPDFDirectoryLoader, PyPDFLoader
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from managers.config_manager import Config
from models.singleton_meta import SingletonMeta


class VectorStoreService(metaclass=SingletonMeta):

    async def create(config: Config, to_reembed=False):
        instance = VectorStoreService(config=config)
        await instance._record_manager.acreate_schema()
        if to_reembed:
            await instance.aadd_to_vector_store()
        return instance

    def __init__(self, config: Config):
        self.config = config
        connection = config.get_value("vector_store")["conn_str"]
        if connection == "no_free_database":
            connection = os.getenv("POSTGRES_TEG")
        collection_name = config.get_value("vector_store")["collection_name"]
        embeddings = GoogleGenerativeAIEmbeddings(model=config.get_value("model_name"))
        # environment must have GOOGLE_API_KEY variable or pass it throgh kwargs

        self._async_engine = create_async_engine(
            connection,
            pool_size=10,
            pool_pre_ping=True,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
        )

        self._vector_store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=self._async_engine,
            use_jsonb=True,
            create_extension=True,
            async_mode=True,
        )

        self._record_manager = SQLRecordManager(
            engine=self._async_engine,
            namespace=config.get_value("vector_store")["namespace"],
            async_mode=True,
        )

        self.splitter = RecursiveCharacterTextSplitter(
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

    async def aadd_to_vector_store(self, path=None):
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
        splitted_docs = [
            Document(
                page_content=doc.page_content,
                metadata={
                    **doc.metadata,
                    "source": os.path.basename(doc.metadata["source"]),
                },
            )
            for doc in loader.load_and_split(self.splitter)
        ]

        return aindex(
            docs_source=splitted_docs,
            record_manager=self._record_manager,
            cleanup="incremental",
            source_id_key="source",
            vector_store=self.vector_store,
        )

    async def save_file_to_vector_store(self, file: UploadFile, file_type: str):
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_type) as tmp:
            tmp.write(await file.read())
            tmp.flush()
            if file_type == ".pdf":
                loader = PyPDFLoader(file_path=tmp.name)
            elif file_type == ".txt":
                loader = TextLoader(file_path=tmp.name)
            else:
                raise NotImplementedError(
                    f"Support for this {file.content_type} type is not implemented yet"
                )
            splitted_docs = [
                Document(
                    page_content=doc.page_content,
                    metadata={**doc.metadata, "source": file.filename},
                )
                for doc in loader.load_and_split(self.splitter)
            ]

            return await aindex(
                docs_source=splitted_docs,
                record_manager=self._record_manager,
                cleanup="incremental",
                source_id_key="source",
                vector_store=self.vector_store,
                batch_size=len(splitted_docs),
            )

    @property
    def vector_store(self) -> VectorStore:
        return self._vector_store

    def as_retriever(self, **kwargs) -> BaseRetriever:
        return self.vector_store.as_retriever(kwargs=kwargs)
