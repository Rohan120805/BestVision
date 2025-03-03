from django.db import models

class Child(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    admission_date = models.DateField()
    
    def __str__(self):
        return self.name

class Resource(models.Model):
    RESOURCE_TYPES = [
        ('FOOD', 'Food'),
        ('CLOTHING', 'Clothing'),
        ('EDUCATION', 'Education'),
        ('MONEY', 'Money'),
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    quantity = models.FloatField()
    unit = models.CharField(max_length=20)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.name} ({self.type})"

class Requirement(models.Model):
    REQUIREMENT_TYPES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('SEASONAL', 'Seasonal'),
    ]
    
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    quantity_per_child = models.FloatField()
    frequency = models.CharField(max_length=20, choices=REQUIREMENT_TYPES)
    
    def __str__(self):
        return f"{self.resource.name} requirement"

class Allocation(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    quantity = models.FloatField()
    date_allocated = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"Allocation for {self.child.name}"

