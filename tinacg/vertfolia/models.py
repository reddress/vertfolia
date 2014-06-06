from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# FIXME: add view for last 5 transactions added

# Transactions prior to 10 years ago may be ignored
# FIXME to fixed date like Jan. 1, 1900
MIN_DATE = timezone.now() - timedelta(days=3650)
MAX_DATE = timezone.now() + timedelta(days=3650)

class Currency(models.Model):
    class Meta:
        verbose_name_plural = "Currencies"
    long_name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=8)
    
    def __str__(self):
        return self.short_name

class Account(models.Model):
    user = models.ForeignKey(User)
    long_name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=10)
    sign_modifier = models.IntegerField(default=1)
    parent = models.ForeignKey('self', null=True, blank=True,
                               related_name='children')

    def __str__(self):
        return self.short_name

class Transaction(models.Model):
    user = models.ForeignKey(User)
    description = models.CharField(max_length=200)
    date = models.DateTimeField(default=timezone.now)
    value = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.ForeignKey(Currency)
    debit = models.ForeignKey(Account, related_name="+")
    credit = models.ForeignKey(Account, related_name="+")
    
    def __str__(self):
        fmt_string = "%s/%s/%s: %.2f %s / %s - %s"
        return fmt_string % (self.date.day, self.date.month, self.date.year,
                             self.value,
                             self.debit, self.credit, self.description[:80],)

class MoneyUnit:
    def __init__(amount, currency):
        self.amount = amount
        self.currency = currency
        
    def add_to(other_moneyunit):
        if other_moneyunit.currency == self.currency:
            return MoneyUnit(other_moneyunit.amount + self.amount)
        else:
            error_msg = "Adding amounts of different currencies is not supported."
            raise ValueError(error_msg)
        
# def account_balance_change(user, account,
#                            start_date=MIN_DATE, end_date=MAX_DATE):
#     balance_change = {}

#     for currency in Currency.objects.all():
#         balance_change[currency.short_name] = 0
        
#     debit_transactions = (Transaction.objects.select_related('debit',
#                                                              'currency',
#                                                              'parent')
#                           .filter(user=user,
#                                   date__gte=start_date, date__lte=end_date,
#                                   debit=account))
#     credit_transactions = (Transaction.objects.select_related('credit',
#                                                               'currency',
#                                                               'parent')
#                            .filter(user=user,
#                                    date__gte=start_date, date__lte=end_date,
#                                    credit=account))
#     for transaction in debit_transactions:
#         balance_change[transaction.currency.short_name] += (
#             transaction.value * account.sign_modifier) 
               
#     for transaction in credit_transactions:
#         balance_change[transaction.currency.short_name] -= (
#             transaction.value * account.sign_modifier)

#     children = account.children.all()
    
#     if len(children) > 0:
#         for currency in Currency.objects.all():
#             for child in children:
#                 balance_change[currency.short_name] += (
#                     account_balance_change(user, child,
#                                            start_date,
#                                            end_date)[currency.short_name])

#     return balance_change

# def all_accounts_balance_change(user, balance_changes={}, start_date=MIN_DATE,
#                                 end_date=MAX_DATE):
#     for account in Account.objects.filter(user=user):
#         if not account.id in balance_changes:
#             balance_changes[account.id] = account_balance_change(
#                 user, account, start_date, end_date)
#         else:
#             print("found id " + account.id)
#     return balance_changes

def leaf_to_root_balance_change(user, start_date=MIN_DATE, end_date=MAX_DATE):
    transactions = (Transaction.objects.select_related('debit', 'credit',
                                                       'currency', 'parent')
                    .filter(user=user,
                            date__gte=start_date, date__lte=end_date))
    balance_changes = {}

    # initialize balance_changes
    accounts = Account.objects.filter(user=user)
    for account in accounts:
        balance_changes[account.id] = {}
        
    currencies = Currency.objects.all()
    for account in accounts:
        for currency in currencies:
            balance_changes[account.id][currency.short_name] = 0
    
    for transaction in transactions:
        debit = transaction.debit
        while debit:
            balance_changes[debit.id][transaction.currency.short_name] += transaction.value * transaction.debit.sign_modifier
            debit = debit.parent

        credit = transaction.credit
        while credit:
            balance_changes[credit.id][transaction.currency.short_name] -= transaction.value * transaction.credit.sign_modifier
            credit = credit.parent

    return balance_changes

def leaf_to_root_balance_change_JSON(user, start_date=MIN_DATE, end_date=MAX_DATE):
    balance_changes = leaf_to_root_balance_change(user, start_date, end_date)

    balance_changes_JSON = {}

    for account_id in balance_changes:
        JSON_str = ""
        for currency in balance_changes[account_id]:
            if balance_changes[account_id][currency] != 0:
                JSON_str += "%s %.2f " % (currency, balance_changes[account_id][currency])
        balance_changes_JSON[account_id] = JSON_str

    return balance_changes_JSON
