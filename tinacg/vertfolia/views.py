import traceback
import json

from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from django.utils import timezone

from .models import Account, Currency, Transaction
from .models import get_balance_changes

def print_balance_change(balance_change):
    output_str = ""
    for currency in balance_change:
        if balance_change[currency] != 0:
            output_str += "%s %.2f " % (currency, balance_change[currency])
    return output_str

# FIXME Login required, login page
def index(request):
    top_account = Account.objects.get(parent=None, user=request.user)
    account_balances = get_balance_changes(request.user,
                                           end_date=timezone.now())
    account_short_names = '","'.join((map(lambda x: getattr(x, 'short_name'),
                                Account.objects.filter(user=request.user)
                                .order_by("short_name"))))
    
    return render(request, 'vertfolia/index.html',
                  { 'top_account': top_account,
                    'account_balances': account_balances,
                    'account_short_names': account_short_names,
                    'time': timezone.now(),
                    })

def add_transaction(request):
    try:
        currency = Currency.objects.get(pk=1)

        # use account primary key (id)
        # debit_account = Account.objects.get(pk=int(request.POST["debit"]))
        # credit_account = Account.objects.get(pk=int(request.POST["credit"]))

        # use short name
        debit_account = Account.objects.get(user=request.user,
                                short_name__iexact=request.POST["debit"])
        credit_account = Account.objects.get(user=request.user,
                                short_name__iexact=request.POST["credit"])

        new_transaction = Transaction(user=request.user,
                                  description=request.POST["description"],
                                  date=timezone.now(),  # FIXME use Unix time?
                                  value=request.POST["value"],
                                  currency=currency,
                                  debit=debit_account,
                                  credit=credit_account,)
        new_transaction.save()

        new_balances = {}
        
        # while debit_account:
        #     new_balances[debit_account.pk] = print_balance_change(
        #         account_balance_change(request.user, debit_account,
        #                                end_date=timezone.now()))
        #     debit_account = debit_account.parent

        # while credit_account:
        #     new_balances[credit_account.pk] = print_balance_change(
        #         account_balance_change(request.user, credit_account,
        #                                end_date=timezone.now()))
        #     credit_account = credit_account.parent

        new_balances = get_balance_changes(request.user,
                                           end_date=timezone.now())
        if request.is_ajax():
            return HttpResponse(json.dumps(new_balances),
                                mimetype="application/json")
        return HttpResponse("Not an ajax request.")

    except Exception:
        print(Exception)
        print(traceback.format_exc())
        return HttpResponseServerError("An error has occurred while adding a transaction")

def refresh_tree(request):
    # print balances for given start and end dates
    pass
    
