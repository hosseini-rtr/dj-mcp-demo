
import os
import sys
from pathlib import Path

import django
from mcp.server.mcpserver import MCPServer

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.db.models import Count, Sum, Q

from core import settings
from sample.models import Customer, Order


mcp = MCPServer("DJ-MCP")

print("MCP Database:", settings.DATABASES["default"]["NAME"])


def serialize_customer(customer):
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "created_at": customer.created_at.isoformat(),
    }


def serialize_order(order):
    return {
        "id": order.id,
        "customer": {
            "id": order.customer_id,
            "name": order.customer.name,
            "email": order.customer.email,
        },
        "amount": str(order.amount),
        "status": order.status,
        "created_at": order.created_at.isoformat(),
    }


def paginate(queryset, limit, offset):
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    total = queryset.count()
    items = queryset[offset:offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": items,
    }


@mcp.tool()
def ping() -> dict:
    """Check whether the MCP server is running."""
    return {
        "status": "ok",
        "server": mcp.name,
    }


@mcp.tool()
def search_customers(query: str, limit: int = 10) -> dict:
    """
    Search customers by name or email.
    Use this when the user provides a customer name or email
    but does not know the customer ID.
    """
    limit = max(1, min(limit, 100))

    customers = Customer.objects.filter(
        Q(name__icontains=query) | Q(email__icontains=query)
    ).order_by("id")[:limit]

    return {
        "query": query,
        "count": len(customers),
        "results": [
            serialize_customer(customer)
            for customer in customers
        ],
    }


@mcp.tool()
def list_customers(limit: int = 10, offset: int = 0) -> dict:
    """
    List customers with pagination.
    Use this when the user asks to see customers or browse the customer list.
    """
    result = paginate(
        Customer.objects.order_by("id"),
        limit,
        offset,
    )

    return {
        "total": result["total"],
        "limit": result["limit"],
        "offset": result["offset"],
        "results": [
            serialize_customer(customer)
            for customer in result["results"]
        ],
    }


@mcp.tool()
def get_customer(customer_id: int) -> dict:
    """
    Retrieve a customer by ID, including basic customer information.
    Use this when the customer ID is known.
    """
    try:
        customer = Customer.objects.get(id=customer_id)
        return serialize_customer(customer)
    except Customer.DoesNotExist:
        return {
            "error": f"Customer with ID {customer_id} does not exist."
        }


@mcp.tool()
def get_order(order_id: int) -> dict:
    """
    Retrieve an order by ID, including its customer information,
    amount, status and creation date.
    """
    try:
        order = Order.objects.select_related("customer").get(id=order_id)
        return serialize_order(order)
    except Order.DoesNotExist:
        return {
            "error": f"Order with ID {order_id} does not exist."
        }


@mcp.tool()
def list_orders(
    customer_id: int = 0,
    status: str = "",
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """
    List orders with optional filters.
    customer_id: Filter by customer ID. Use 0 for all customers.
    status: Filter by pending, paid or cancelled. Empty string means all statuses.
    limit and offset: Pagination parameters.
    """
    queryset = Order.objects.select_related("customer").order_by("-created_at")

    if customer_id > 0:
        queryset = queryset.filter(customer_id=customer_id)

    if status:
        valid_statuses = [choice[0] for choice in Order.Status.choices]

        if status not in valid_statuses:
            return {
                "error": "Invalid status.",
                "valid_statuses": valid_statuses,
            }

        queryset = queryset.filter(status=status)

    result = paginate(queryset, limit, offset)

    return {
        "total": result["total"],
        "limit": result["limit"],
        "offset": result["offset"],
        "filters": {
            "customer_id": customer_id or None,
            "status": status or None,
        },
        "results": [
            serialize_order(order)
            for order in result["results"]
        ],
    }


@mcp.tool()
def get_order_stats(customer_id: int = 0) -> dict:
    """
    Get order statistics, including total orders, counts by status,
    total order amount and paid order amount.
    Optionally filter statistics by customer ID.
    """
    queryset = Order.objects.all()

    if customer_id > 0:
        queryset = queryset.filter(customer_id=customer_id)

    stats = queryset.aggregate(
        total_orders=Count("id"),
        pending_orders=Count("id", filter=Q(status=Order.Status.PENDING)),
        paid_orders=Count("id", filter=Q(status=Order.Status.PAID)),
        cancelled_orders=Count("id", filter=Q(status=Order.Status.CANCELLED)),
        total_amount=Sum("amount"),
        paid_amount=Sum(
            "amount",
            filter=Q(status=Order.Status.PAID),
        ),
    )

    return {
        "customer_id": customer_id or None,
        "total_orders": stats["total_orders"],
        "pending_orders": stats["pending_orders"],
        "paid_orders": stats["paid_orders"],
        "cancelled_orders": stats["cancelled_orders"],
        "total_amount": str(stats["total_amount"] or 0),
        "paid_amount": str(stats["paid_amount"] or 0),
    }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8001,
        stateless_http=True,
        json_response=True,
    )

