"""
Document management use cases for PyTaskAI application layer.
"""

from typing import List, Optional

from pytaskai.application.dto.task_dto import (
    DocumentCreateDTO,
    DocumentResponseDTO,
    DocumentUpdateDTO,
)
from pytaskai.domain.entities.task import Document
from pytaskai.domain.repositories.task_repository import TaskManagementRepository
from pytaskai.domain.services.task_service import DocumentService


class DocumentManagementUseCase:
    """
    Use case for document management operations (CRUD).

    This use case orchestrates domain services and repositories
    to provide document management functionality for external adapters.
    """

    def __init__(
        self,
        repository: TaskManagementRepository,
        document_service: DocumentService,
    ) -> None:
        self._repository = repository
        self._document_service = document_service

    async def create_document(
        self, document_data: DocumentCreateDTO
    ) -> DocumentResponseDTO:
        """
        Create a new document.

        Args:
            document_data: Document creation data

        Returns:
            Created document as DTO

        Raises:
            ValueError: If document data is invalid
        """
        document = await self._repository.docs.create_doc(
            title=document_data.title,
            text=document_data.text,
            folder=document_data.folder,
            is_draft=document_data.is_draft,
        )

        return self._document_to_dto(document)

    async def get_document(self, document_id: str) -> Optional[DocumentResponseDTO]:
        """
        Get a document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document as DTO or None if not found
        """
        document = await self._repository.docs.get_doc(document_id)
        return self._document_to_dto(document) if document else None

    async def list_documents(
        self,
        folder: Optional[str] = None,
        search: Optional[str] = None,
        include_drafts: bool = True,
        include_trash: bool = False,
    ) -> List[DocumentResponseDTO]:
        """
        List documents with optional filtering.

        Args:
            folder: Optional folder filter
            search: Optional search term
            include_drafts: Whether to include draft documents
            include_trash: Whether to include trashed documents

        Returns:
            List of documents as DTOs
        """
        # Apply filters
        kwargs = {}
        if folder:
            kwargs["folder"] = folder
        if search:
            kwargs["search"] = search

        documents = await self._repository.docs.list_docs(**kwargs)

        # Apply additional filtering
        if not include_drafts:
            documents = [doc for doc in documents if not doc.is_draft]
        if not include_trash:
            documents = [doc for doc in documents if not doc.in_trash]

        return [self._document_to_dto(doc) for doc in documents]

    async def update_document(
        self, update_data: DocumentUpdateDTO
    ) -> DocumentResponseDTO:
        """
        Update an existing document.

        Args:
            update_data: Document update data

        Returns:
            Updated document as DTO

        Raises:
            ValueError: If document not found or update data is invalid
        """
        # Check if document exists
        current_document = await self._repository.docs.get_doc(update_data.document_id)
        if not current_document:
            raise ValueError(f"Document {update_data.document_id} not found")

        # Prepare update parameters
        kwargs = {"doc_id": update_data.document_id}

        if update_data.title is not None:
            kwargs["title"] = update_data.title
        if update_data.text is not None:
            kwargs["text"] = update_data.text
        if update_data.folder is not None:
            kwargs["folder"] = update_data.folder
        if update_data.is_draft is not None:
            kwargs["is_draft"] = update_data.is_draft

        # Update document through repository
        updated_document = await self._repository.docs.update_doc(**kwargs)

        return self._document_to_dto(updated_document)

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document (move to trash).

        Args:
            document_id: Document identifier

        Returns:
            True if document was deleted

        Raises:
            ValueError: If document not found
        """
        document = await self._repository.docs.get_doc(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        return await self._repository.docs.delete_doc(document_id)

    async def get_documents_by_folder(self, folder: str) -> List[DocumentResponseDTO]:
        """
        Get all documents in a specific folder using domain service.

        Args:
            folder: Folder name

        Returns:
            List of documents as DTOs
        """
        documents = await self._document_service.get_docs_by_folder(folder)
        return [self._document_to_dto(doc) for doc in documents]

    async def search_documents_content(
        self, search_term: str
    ) -> List[DocumentResponseDTO]:
        """
        Search documents by content using domain service.

        Args:
            search_term: Term to search for

        Returns:
            List of matching documents as DTOs
        """
        documents = await self._document_service.search_docs_content(search_term)
        return [self._document_to_dto(doc) for doc in documents]

    async def get_empty_documents(self) -> List[DocumentResponseDTO]:
        """
        Get all empty documents using domain service.

        Returns:
            List of empty documents as DTOs
        """
        documents = await self._document_service.get_empty_docs()
        return [self._document_to_dto(doc) for doc in documents]

    async def duplicate_document(
        self,
        source_document_id: str,
        new_title: Optional[str] = None,
        target_folder: Optional[str] = None,
    ) -> DocumentResponseDTO:
        """
        Duplicate an existing document using domain service.

        Args:
            source_document_id: ID of document to duplicate
            new_title: Optional new title for duplicated document
            target_folder: Optional target folder for duplicated document

        Returns:
            Duplicated document as DTO

        Raises:
            ValueError: If source document not found
        """
        duplicated_document = await self._document_service.duplicate_doc(
            source_document_id, new_title, target_folder
        )
        return self._document_to_dto(duplicated_document)

    def _document_to_dto(self, document: Document) -> DocumentResponseDTO:
        """Convert domain Document entity to DocumentResponseDTO."""
        return DocumentResponseDTO(
            id=document.id,
            title=document.title,
            text=document.text,
            folder=document.folder,
            is_draft=document.is_draft,
            in_trash=document.in_trash,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
