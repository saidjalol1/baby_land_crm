from django.db import models


class Province(models.Model):
    name = models.CharField(max_length=250)
    def __str__(self):
        return self.name
    
    
class Regions(models.Model):
    name = models.CharField(max_length=250)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name="regions")
    
    def __str__(self):
        return self.province.name + "-" + self.name
    

class Shop(models.Model):
    name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)
    
    region = models.ForeignKey(Regions, on_delete=models.CASCADE, related_name="shops")
    
    def __str__(self):
        return self.name + " " +  self.last_name + "-" + self.region.name
    

    

