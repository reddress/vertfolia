from django.shortcuts import render
from django.http import HttpResponse

from .models import Account, all_accounts_balance_change

def index(request):
    top_account = Account.objects.get(short_name="tina")
    account_balances = all_accounts_balance_change()

    return render(request, 'vertfolia/index.html',
                  { 'top_account': top_account,
                    'account_balances': account_balances,
                    })
