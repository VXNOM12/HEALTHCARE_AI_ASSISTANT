# data_processor.py (Data Management Layer)
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import tempfile

class DataProcessor:
    def __init__(self):
        self.embedder = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}  # Or "cuda" if you have GPU available
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    def process_files(self, uploaded_files):
        documents = []
        
        for file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file.getvalue())
                loader = self._get_loader(file.type, temp_file.name)
                documents.extend(loader.load())
        
        return self.text_splitter.split_documents(documents)

    def _get_loader(self, file_type, file_path):
        loaders = {
            "application/pdf": PyPDFLoader,
            "text/plain": TextLoader,
            "text/csv": CSVLoader
        }
        return loaders[file_type](file_path)

    def create_vector_store(self, documents):
        return Chroma.from_documents(
            documents=documents,
            embedding=self.embedder,
            persist_directory="./chroma_db"
        )

    def retrieve_context(self, query, vector_store, top_k=3):
        results = vector_store.similarity_search(query, k=top_k)
        return "\n".join([doc.page_content for doc in results])
