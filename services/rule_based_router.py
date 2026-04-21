from models.routing import RouteResponse


class RuleBasedRouter:
    async def route(self, user_input: str) -> RouteResponse:
        lowered = user_input.lower().strip()

        if any(word in lowered for word in ["extract", "find email", "find order", "pull fields"]):
            return RouteResponse(route="extract")

        if any(word in lowered for word in ["classify", "category", "label this"]):
            return RouteResponse(route="classify")

        if any(word in lowered for word in ["summarize", "summary", "short version"]):
            return RouteResponse(route="summarize")

        if "?" in lowered or lowered.startswith(("what", "why", "how", "when", "where", "who")):
            return RouteResponse(route="answer")

        return RouteResponse(route="answer")