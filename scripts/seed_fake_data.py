
import os
import sys
import random
import argparse
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from django.db import transaction
from sample.models import Customer, Order


FIRST_NAMES = [
    "Ali", "Hossein", "Mohammad", "Reza", "Sara",
    "Maryam", "Amir", "Nima", "Arman", "Negar",
    "John", "David", "Emma", "Sophia", "James",
]

LAST_NAMES = [
    "Ahmadi", "Hosseini", "Karimi", "Mohammadi",
    "Smith", "Johnson", "Brown", "Wilson", "Taylor",
]

STATUSES = [
    Order.Status.PENDING,
    Order.Status.PAID,
    Order.Status.CANCELLED,
]


def generate_customers(count):
    customers = []

    for index in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        email = f"customer{index + 1}@example.com"

        customer, _ = Customer.objects.get_or_create(
            email=email,
            defaults={
                "name": f"{first_name} {last_name}",
            },
        )

        customers.append(customer)

    return customers


def generate_orders(customers, count):
    orders = []

    for _ in range(count):
        customer = random.choice(customers)

        amount = Decimal(
            random.randrange(1000, 50000000)
        ) / Decimal("100")

        orders.append(
            Order(
                customer=customer,
                amount=amount,
                status=random.choices(
                    STATUSES,
                    weights=[30, 55, 15],
                    k=1,
                )[0],
            )
        )

    Order.objects.bulk_create(orders)


def main():
    parser = argparse.ArgumentParser(
        description="Generate fake customers and orders."
    )

    parser.add_argument("--customers", type=int, default=30)
    parser.add_argument("--orders", type=int, default=100)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing orders and customers before seeding.",
    )

    args = parser.parse_args()

    if args.customers < 1 or args.orders < 0:
        parser.error("Customers must be positive and orders cannot be negative.")

    with transaction.atomic():
        if args.reset:
            Order.objects.all().delete()
            Customer.objects.all().delete()

        customers = generate_customers(args.customers)
        generate_orders(customers, args.orders)

    print("Fake data generated successfully!")
    print(f"Customers in database: {Customer.objects.count()}")
    print(f"Orders in database: {Order.objects.count()}")


if __name__ == "__main__":
    main()
