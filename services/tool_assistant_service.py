import re
from typing import Any

from tools.order_tools import (
    check_refund_eligibility,
    confirm_pending_refund_request,
    create_pending_refund_request,
    get_order_status,
)


ORDER_ID_PATTERN = re.compile(r"\bORD-\d+\b", re.IGNORECASE)
PENDING_ACTION_PATTERN = re.compile(r"\bPEND-\d+\b", re.IGNORECASE)

TOOL_GET_ORDER_STATUS = "get_order_status"
TOOL_CHECK_REFUND_ELIGIBILITY = "check_refund_eligibility"
TOOL_CREATE_PENDING_REFUND_REQUEST = "create_pending_refund_request"
TOOL_CONFIRM_PENDING_REFUND_REQUEST = "confirm_pending_refund_request"


class ToolAssistantService:
    async def answer(self, message: str) -> dict[str, Any]:
        pending_action_id = self._extract_pending_action_id(message)

        if pending_action_id and self._is_confirmation(message):
            return self._handle_pending_refund_confirmation(pending_action_id)

        order_id = self._extract_order_id(message)

        if order_id is None:
            return self._build_response(
                answer="Please provide an order ID so I can help with your request.",
                tool_calls=[],
            )

        if self._is_refund_creation_request(message):
            return self._handle_pending_refund_creation(order_id)

        if self._is_refund_question(message):
            tool_result = check_refund_eligibility(order_id)

            return self._build_response(
                answer=self._format_refund_answer(tool_result),
                tool_calls=[
                    {
                        "tool_name": TOOL_CHECK_REFUND_ELIGIBILITY,
                        "result": tool_result,
                    }
                ],
            )

        tool_result = get_order_status(order_id)

        return self._build_response(
            answer=self._format_status_answer(tool_result),
            tool_calls=[
                {
                    "tool_name": TOOL_GET_ORDER_STATUS,
                    "result": tool_result,
                }
            ],
        )

    def _handle_pending_refund_creation(self, order_id: str) -> dict[str, Any]:
        tool_result = create_pending_refund_request(order_id)

        return self._build_response(
            answer=self._format_pending_refund_creation_answer(tool_result),
            tool_calls=[
                {
                    "tool_name": TOOL_CREATE_PENDING_REFUND_REQUEST,
                    "result": tool_result,
                }
            ],
        )

    def _handle_pending_refund_confirmation(self, pending_action_id: str) -> dict[str, Any]:
        tool_result = confirm_pending_refund_request(pending_action_id)

        return self._build_response(
            answer=self._format_pending_refund_confirmation_answer(tool_result),
            tool_calls=[
                {
                    "tool_name": TOOL_CONFIRM_PENDING_REFUND_REQUEST,
                    "result": tool_result,
                }
            ],
        )

    def _build_response(
        self,
        answer: str,
        tool_calls: list[dict[str, Any]],
    ) -> dict[str, Any]:
        last_tool_call = tool_calls[-1] if tool_calls else None

        return {
            "answer": answer,
            "tool_called": last_tool_call["tool_name"] if last_tool_call else None,
            "tool_result": last_tool_call["result"] if last_tool_call else None,
            "tool_calls": tool_calls,
        }

    def _extract_order_id(self, message: str) -> str | None:
        match = ORDER_ID_PATTERN.search(message)

        if match is None:
            return None

        return match.group(0).upper()

    def _extract_pending_action_id(self, message: str) -> str | None:
        match = PENDING_ACTION_PATTERN.search(message)

        if match is None:
            return None

        return match.group(0).upper()

    def _is_confirmation(self, message: str) -> bool:
        normalized_message = message.lower()

        confirmation_terms = [
            "confirm",
            "yes",
            "approve",
            "go ahead",
            "submit",
        ]

        return any(term in normalized_message for term in confirmation_terms)

    def _is_refund_question(self, message: str) -> bool:
        normalized_message = message.lower()

        refund_terms = [
            "refund",
            "money back",
            "return",
            "cancel",
        ]

        return any(term in normalized_message for term in refund_terms)

    def _is_refund_creation_request(self, message: str) -> bool:
        normalized_message = message.lower()

        creation_terms = [
            "i want a refund",
            "i need a refund",
            "request a refund",
            "submit a refund",
            "create a refund",
            "start a refund",
            "please refund",
            "refund my order",
            "refund this order",
        ]

        return any(term in normalized_message for term in creation_terms)

    def _format_status_answer(self, tool_result: dict[str, object]) -> str:
        if not tool_result["found"]:
            return f"I could not find order {tool_result['order_id']}."

        return (
            f"Order {tool_result['order_id']} is currently "
            f"{tool_result['status']}. Estimated delivery is "
            f"{tool_result['estimated_delivery']}."
        )

    def _format_refund_answer(self, tool_result: dict[str, object]) -> str:
        if not tool_result["found"]:
            return f"I could not find order {tool_result['order_id']}."

        if tool_result["eligible"]:
            return (
                f"Order {tool_result['order_id']} appears to be eligible "
                f"for a refund. Reason: {tool_result['reason']}"
            )

        return (
            f"Order {tool_result['order_id']} does not appear to be eligible "
            f"for a refund. Reason: {tool_result['reason']}"
        )

    def _format_pending_refund_creation_answer(
        self,
        tool_result: dict[str, object],
    ) -> str:
        if not tool_result["created"]:
            return str(tool_result["message"])

        return (
            f"Order {tool_result['order_id']} is eligible for a refund. "
            f"Please confirm {tool_result['pending_action_id']} if you want me "
            f"to submit the refund request."
        )

    def _format_pending_refund_confirmation_answer(
        self,
        tool_result: dict[str, object],
    ) -> str:
        if not tool_result["confirmed"]:
            return str(tool_result["message"])

        return (
            f"Refund request {tool_result['refund_request_id']} has been submitted "
            f"for order {tool_result['order_id']}."
        )