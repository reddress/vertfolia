from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.models import User

from .models import Account, all_accounts_balance_change

# FIXME: get top account for current user name

def index(request):
    user = User.objects.get(username=request.user.username)

    top_account = Account.objects.get(short_name="tina")
    account_balances = all_accounts_balance_change(user)

    return render(request, 'vertfolia/index.html',
                  { 'top_account': top_account,
                    'account_balances': account_balances,
                    })
