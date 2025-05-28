from abc import ABC, abstractmethod

class TextExtractor(ABC):
    """
    Abstract base class for text extraction from different file types.
    """

    @abstractmethod
    def extract(self, file_path: str) -> str:
        """
        Extracts text content from the given file.

        Args:
            file_path (str): The path to the file from which to extract text.

        Returns:
            str: The extracted text content.

        Raises:
            FileNotFoundError: If the file_path does not exist.
            Exception: For any errors during the extraction process specific to the implementation.
        """
        pass 