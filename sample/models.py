from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
        
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,related_name="orders")
    amount = models.DecimalField(max_digits=12,decimal_places=2)
    status = models.CharField(max_length=20,choices=Status.choices,default=Status.PENDING)
    created_at=models.DateTimeField(auto_now_add=True)
    