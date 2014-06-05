from datetime import datetime

from django.db import models

# Create your models here.

class Currency(models.Model):
    long_name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=8)
    
    def __str__(self):
        return self.short_name

###
# How to link account and transaction to Django User? See mapcal
###
# add user field to both because there may be pages that show details
# for individual entries
###
class Account(models.Model):
    long_name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=10)
    parent = models.ForeignKey(Account, null=True, blank=True)

    def __str__(self):
        return self.short_name

class Transaction(models.Model):
    description = models.CharField(max_length=200)
    date = models.DateTimeField(default=datetime.now)
    value = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.ForeignKey(Currency)
    debit = models.ForeignKey(Account, related_name="+")
    credit = models.ForeignKey(Account, related_name="+")
    
    def __str__(self):
        fmt_string = "%s/%s/%s: %.2f %s / %s - %s"
        return fmt_string % (self.date.day, self.date.month, self.date.year,
                             self.value,
                             self.debit, self.credit, self.description[:80],)
