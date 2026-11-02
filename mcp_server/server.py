import os
from pathlib import Path
import sys

import django
from mcp.server.mcpserver import MCPServer
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from core import settings
from sample.models import Customer, Order

mcp = MCPServer("DJ-MCP")


print("MCP Database:", settings.DATABASES["default"]["NAME"])
    
@mcp.tool()
def ping()-> dict:
    """Check whether the server is running and responsive."""
    return {"status": "ok","server": mcp.name}

@mcp.tool()
def get_customer(customer_id:int)-> dict:
    """Retrieve a customer by ID."""
    try:
        customer = Customer.objects.get(id=customer_id)
        return {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "created_at": customer.created_at.isoformat(),
        }
    except Customer.DoesNotExist:
        return {"error": f"Customer with ID {customer_id} does not exist."}


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8001,
        stateless_http=True,
        json_response=True,
    )