from django.contrib import admin
from .models import Account, Currency, Transaction

# Register your models here.
admin.site.register(Account)
admin.site.register(Currency)
admin.site.register(Transaction)
