from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import utc, localtime

# Transactions prior to 1901 are ignored
MIN_DATE = datetime(1901, 1, 1).replace(tzinfo=timezone.utc)

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
        local_time = localtime(datetime(self.date.year, self.date.month,
                                        self.date.day,
                                        self.date.hour, self.date.minute,
                                        self.date.second, 0, utc))

        # date_format = "%a %d/%m/%y %H:%M"
        date_format = "%a %d/%m/%y"
        fmt_string = "%s %s %.2f %s/%s %s"
        
        return fmt_string % (local_time.strftime(date_format),
                             self.currency.short_name,
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

# REMOVED: easy to understand but very slow
#
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

def leaf_to_root_balance_changes(user, start_date=MIN_DATE, end_date=timezone.now()):
    transactions = (Transaction.objects.select_related('debit', 'credit',
                                                       'currency', 'parent')
                    .filter(user=user,
                            date__gte=start_date, date__lte=end_date))
    balance_changes = {}

    # cache parent ids
    account_parent = {}
    
    # initialize balance_changes and parent id cache
    accounts = Account.objects.filter(user=user)
    for account in accounts:
        balance_changes[account.id] = {}
        if account.parent:
            account_parent[account.id] = account.parent.id
        else:
            account_parent[account.id] = None
        
    currencies = Currency.objects.all()
    for account in accounts:
        for currency in currencies:
            balance_changes[account.id][currency.short_name] = 0
    
    for transaction in transactions:
        debit_id = transaction.debit.id
        while account_parent[debit_id]:
            balance_changes[debit_id][transaction.currency.short_name] += transaction.value * transaction.debit.sign_modifier
            debit_id = account_parent[debit_id]

        credit_id = transaction.credit.id
        while account_parent[credit_id]:
            balance_changes[credit_id][transaction.currency.short_name] -= transaction.value * transaction.credit.sign_modifier
            credit_id = account_parent[credit_id]

    return balance_changes

def get_balance_changes(user, start_date=MIN_DATE, end_date=timezone.now()):
    balance_changes = leaf_to_root_balance_changes(user, start_date, end_date)

    balance_changes_formatted = {}

    for account_id in balance_changes:
        formatted_str = ""
        for currency in balance_changes[account_id]:
            if balance_changes[account_id][currency] != 0:
                formatted_str += "%s %.2f " % (currency, balance_changes[account_id][currency])
        balance_changes_formatted[account_id] = formatted_str

    return balance_changes_formatted

def add_account_from_string(user, account_data_string):
    account_data = account_data_string.split(";")
    new_account = Account(user=user, long_name=account_data[0],
                          short_name=account_data[1],
                          sign_modifier=int(account_data[2]),
                          parent=Account.objects.get(user=user,
                                                     short_name=account_data[3]))
    new_account.save()

def add_accounts_from_file(user, filename):
    file = open(filename)
    for line in file:
        add_account_from_string(user, line.strip())
    # in python manage.py shell
    # from vertfolia.models import *
    # from django.contrib.auth.models import User
    # tina = User.objects.get(pk=1)
    # add_accounts_from_file(tina, "alesheets_account_dump.txt")

def add_transaction_from_string(user, transaction_data_string):
    transaction_data = transaction_data_string.split(";")
    transaction_date_fields = map(int, transaction_data[0].split("-"))
    transaction_date = datetime(*transaction_date_fields)
    new_transaction = Transaction(user=user,
                                  description=transaction_data[4],
                                  date=transaction_date,
                                  value=transaction_data[1],
                                  currency=Currency.objects.get(pk=1),
                                  debit=Account.objects.get(user=user,
                                            short_name=transaction_data[2]),
                                  credit=Account.objects.get(user=user,
                                            short_name=transaction_data[3]))
    new_transaction.save()

def add_transactions_from_file(user, filename):
    file = open(filename)
    for line in file:
        add_transaction_from_string(user, line.strip())
    # usage: see python shell comments above (for accounts)

def is_parent(parent, account):
    # conceptually simple, but slow
    # return True is parent is account's parent
    if parent == None or account == None:
        return False
    if parent == account.parent:
        return True
    else:
        return is_parent(parent, account.parent)
    
def get_children_accounts(parent):
    user = parent.user
    user_accounts = Account.objects.filter(user=user)
    children = []

    for account in user_accounts:
        if is_parent(parent, account):
            children.append(account)
    return children
