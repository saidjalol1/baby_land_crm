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
    

class Product(models.Model):
    name = models.CharField(max_length=250)
    base_price = models.PositiveIntegerField(default=0)
    sale_price = models.PositiveIntegerField(default=0)
    amount = models.PositiveIntegerField(default=0)
    qr_code_id = models.CharField(max_length=250)
    
    def get_overall(self):
        return self.base_price * self.amount
    
    def __str__(self):
        return self.name
    

class Transaction(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=250)
    amount = models.PositiveIntegerField()
    date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.transaction_type} - {self.amount} on {self.date}"


class Sale(models.Model):
    payment = models.PositiveIntegerField(default=0)
    debt = models.PositiveIntegerField(default=0)
    date_added = models.DateField(auto_now_add=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="sales")
    
    def get_amount(self):
        return sum([i.get_amount() for i in self.items.all()])
    
    def __str__(self):
        return f"{self.date_added} - sotuv - {self.id}"



class SaleItems(models.Model):
    quantity = models.PositiveIntegerField(default=0)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales")
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    
    
    def get_income(self):
        profit = self.product.sale_price - self.product.base_price
        return profit * self.quantity
    
    def get_amount(self):
        overall =  self.product.sale_price * self.quantity
        if overall > 0:
            return overall
        else:
            return 0
    
    def __str__(self) -> str:
        return f"{self.product.name } - {self.id}"
    
class MoneyTransactions(models.Model):
    amount = models.PositiveIntegerField(default=0)
    date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return self.amount