from django.db import models


class Expances(models.Model):
    name = models.CharField(max_length=250)
    amount = models.PositiveIntegerField(default=0)
    date_added = models.DateField()
    
    def __str__(self):
        return self.name
