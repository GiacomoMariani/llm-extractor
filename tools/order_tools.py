from typing import Any

from clients.order_client import create_order_client
from settings import get_settings


settings = get_settings()

ORDER_CLIENT = create_order_client(
    client_type=settings.order_client_type,
    base_url=settings.order_api_base_url,
    api_key=settings.order_api_key,
)


def get_order_status(order_id: str) -> dict[str, Any]:
    normalized_order_id = order_id.upper()
    order = ORDER_CLIENT.get_order(normalized_order_id)

    if order is None:
        return {
            "found": False,
            "order_id": normalized_order_id,
            "message": "Order not found.",
        }

    return {
        "found": True,
        "order_id": normalized_order_id,
        "status": order["status"],
        "estimated_delivery": order["estimated_delivery"],
    }


def check_refund_eligibility(order_id: str) -> dict[str, Any]:
    normalized_order_id = order_id.upper()
    order = ORDER_CLIENT.get_order(normalized_order_id)

    if order is None:
        return {
            "found": False,
            "order_id": normalized_order_id,
            "eligible": False,
            "reason": "Order not found.",
        }

    return {
        "found": True,
        "order_id": normalized_order_id,
        "eligible": order["refund_eligible"],
        "reason": order["refund_reason"],
    }

REFUND_REQUESTS: list[dict[str, object]] = []

def create_refund_request(order_id: str) -> dict[str, object]:
    eligibility = check_refund_eligibility(order_id)

    if not eligibility["found"]:
        return {
            "created": False,
            "order_id": order_id,
            "message": "Refund request could not be created because the order was not found.",
        }

    if not eligibility["eligible"]:
        return {
            "created": False,
            "order_id": order_id,
            "message": f"Refund request could not be created. Reason: {eligibility['reason']}",
        }

    refund_request_id = f"REF-{len(REFUND_REQUESTS) + 1:03d}"

    refund_request = {
        "refund_request_id": refund_request_id,
        "order_id": order_id,
        "status": "submitted",
    }

    REFUND_REQUESTS.append(refund_request)

    return {
        "created": True,
        "refund_request_id": refund_request_id,
        "order_id": order_id,
        "status": "submitted",
        "message": "Refund request submitted successfully.",
    }

def create_refund_request(order_id: str) -> dict[str, object]:
    eligibility = check_refund_eligibility(order_id)

    if not eligibility["found"]:
        return {
            "created": False,
            "order_id": order_id,
            "message": "Refund request could not be created because the order was not found.",
        }

    if not eligibility["eligible"]:
        return {
            "created": False,
            "order_id": order_id,
            "message": f"Refund request could not be created. Reason: {eligibility['reason']}",
        }

    refund_request_id = f"REF-{len(REFUND_REQUESTS) + 1:03d}"

    refund_request = {
        "refund_request_id": refund_request_id,
        "order_id": order_id,
        "status": "submitted",
    }

    REFUND_REQUESTS.append(refund_request)

    return {
        "created": True,
        "refund_request_id": refund_request_id,
        "order_id": order_id,
        "status": "submitted",
        "message": "Refund request submitted successfully.",
    }

def create_refund_request(order_id: str) -> dict[str, object]:
    eligibility = check_refund_eligibility(order_id)

    if not eligibility["found"]:
        return {
            "created": False,
            "order_id": order_id,
            "message": "Refund request could not be created because the order was not found.",
        }

    if not eligibility["eligible"]:
        return {
            "created": False,
            "order_id": order_id,
            "message": f"Refund request could not be created. Reason: {eligibility['reason']}",
        }

    refund_request_id = f"REF-{len(REFUND_REQUESTS) + 1:03d}"

    refund_request = {
        "refund_request_id": refund_request_id,
        "order_id": order_id,
        "status": "submitted",
    }

    REFUND_REQUESTS.append(refund_request)

    return {
        "created": True,
        "refund_request_id": refund_request_id,
        "order_id": order_id,
        "status": "submitted",
        "message": "Refund request submitted successfully.",
    }

def create_refund_request(order_id: str) -> dict[str, object]:
    eligibility = check_refund_eligibility(order_id)

    if not eligibility["found"]:
        return {
            "created": False,
            "order_id": order_id,
            "message": "Refund request could not be created because the order was not found.",
        }

    if not eligibility["eligible"]:
        return {
            "created": False,
            "order_id": order_id,
            "message": f"Refund request could not be created. Reason: {eligibility['reason']}",
        }

    refund_request_id = f"REF-{len(REFUND_REQUESTS) + 1:03d}"

    refund_request = {
        "refund_request_id": refund_request_id,
        "order_id": order_id,
        "status": "submitted",
    }

    REFUND_REQUESTS.append(refund_request)

    return {
        "created": True,
        "refund_request_id": refund_request_id,
        "order_id": order_id,
        "status": "submitted",
        "message": "Refund request submitted successfully.",
    }

PENDING_REFUND_REQUESTS: dict[str, dict[str, object]] = {}


def create_pending_refund_request(order_id: str) -> dict[str, object]:
    eligibility = check_refund_eligibility(order_id)

    if not eligibility["found"]:
        return {
            "created": False,
            "order_id": order_id,
            "message": "Pending refund request could not be created because the order was not found.",
        }

    if not eligibility["eligible"]:
        return {
            "created": False,
            "order_id": order_id,
            "message": f"Pending refund request could not be created. Reason: {eligibility['reason']}",
        }

    pending_action_id = f"PEND-{len(PENDING_REFUND_REQUESTS) + 1:03d}"

    pending_action = {
        "pending_action_id": pending_action_id,
        "order_id": order_id,
        "action": "create_refund_request",
        "status": "pending_confirmation",
    }

    PENDING_REFUND_REQUESTS[pending_action_id] = pending_action

    return {
        "created": True,
        "pending_action_id": pending_action_id,
        "order_id": order_id,
        "action": "create_refund_request",
        "status": "pending_confirmation",
        "message": "Refund request is pending confirmation.",
    }


def confirm_pending_refund_request(pending_action_id: str) -> dict[str, object]:
    pending_action = PENDING_REFUND_REQUESTS.get(pending_action_id)

    if pending_action is None:
        return {
            "confirmed": False,
            "pending_action_id": pending_action_id,
            "message": "Pending refund request was not found.",
        }

    order_id = str(pending_action["order_id"])
    creation_result = create_refund_request(order_id)

    if not creation_result["created"]:
        return {
            "confirmed": False,
            "pending_action_id": pending_action_id,
            "order_id": order_id,
            "message": creation_result["message"],
        }

    del PENDING_REFUND_REQUESTS[pending_action_id]

    return {
        "confirmed": True,
        "pending_action_id": pending_action_id,
        "order_id": order_id,
        "refund_request_id": creation_result["refund_request_id"],
        "status": creation_result["status"],
        "message": "Pending refund request confirmed and submitted.",
    }