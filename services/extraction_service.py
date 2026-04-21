import logging

from models.extraction import ExtractResponse
from services.exceptions import AppServiceError
from services.extractor import TicketExtractor

logger = logging.getLogger(__name__)


class ExtractionService:
    def __init__(self, extractor: TicketExtractor):
        self.extractor = extractor

    async def extract(self, text: str) -> ExtractResponse:
        normalized_text = text.strip()

        try:
            return await self.extractor.extract(normalized_text)
        except Exception as ex:
            logger.exception("Extraction failed for input text.")
            raise AppServiceError("Failed to extract fields.") from ex