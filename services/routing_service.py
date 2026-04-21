import logging

from models.routing import RouteResponse
from services.exceptions import AppServiceError
from services.rule_based_router import RuleBasedRouter

logger = logging.getLogger(__name__)


class RoutingService:
    def __init__(self, router: RuleBasedRouter):
        self.router = router

    async def route(self, user_input: str) -> RouteResponse:
        normalized_input = user_input.strip()

        try:
            return await self.router.route(normalized_input)
        except Exception as ex:
            logger.exception("Routing failed for input text.")
            raise AppServiceError("Failed to route request.") from ex