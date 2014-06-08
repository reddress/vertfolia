import traceback
import json
from datetime import datetime, timedelta
from itertools import chain

from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from django.utils import timezone
from django.utils.timezone import get_default_timezone, localtime, utc
from django.contrib.auth.decorators import login_required

from .models import Account, Currency, Transaction
from .models import get_balance_changes

def print_balance_change(balance_change):
    output_str = ""
    for currency in balance_change:
        if balance_change[currency] != 0:
            output_str += "%s %.2f " % (currency, balance_change[currency])
    return output_str

# FIXME add a login page, update urls.py
@login_required
def index(request):
    top_account = Account.objects.get(parent=None, user=request.user)
    account_balances = get_balance_changes(request.user,
                                           end_date=timezone.now())
    account_short_names = '","'.join((map(lambda x: getattr(x, 'short_name'),
                                Account.objects.filter(user=request.user)
                                .order_by("short_name"))))

    first_transaction_date = (Transaction.objects.filter(user=request.user)
                              .order_by("date")[0].date)


    latest_transactions = (Transaction.objects.filter(user=request.user)
                           .order_by("pk").reverse()[:5])
    
    return render(request, 'vertfolia/index.html',
                  { 'top_account': top_account,
                    'account_balances': account_balances,
                    'account_short_names': account_short_names,
                    'time': timezone.now(),
                    'earliest_date': first_transaction_date,
                    'latest_transactions': latest_transactions,
                    })

@login_required
def add_transaction(request):
    try:
        # FIXME add currency dropdown
        currency = Currency.objects.get(pk=1)

        # use account primary key (id)
        # debit_account = Account.objects.get(pk=int(request.POST["debit"]))
        # credit_account = Account.objects.get(pk=int(request.POST["credit"]))

        # use short name
        debit_account = Account.objects.get(user=request.user,
                                short_name__iexact=request.POST["debit"])
        credit_account = Account.objects.get(user=request.user,
                                short_name__iexact=request.POST["credit"])

        year_month_day = list(map(int, request.POST["day"].split("/")))[::-1]
        hour_minute = list(map(int, request.POST["time"].split(":")))

        add_date = localtime(datetime(*(year_month_day+hour_minute),
                                      tzinfo=get_default_timezone()), utc)
            
        new_transaction = Transaction(user=request.user,
                                  description=request.POST["description"],
                                  # date=timezone.now(),
                                  date=add_date,
                                  value=request.POST["value"],
                                  currency=currency,
                                  debit=debit_account,
                                  credit=credit_account,)
        new_transaction.save()

        # new_balances = get_balance_changes(request.user,
        #                                    end_date=timezone.now())
        if request.is_ajax():
            # return HttpResponse(json.dumps(new_balances),
            #                    mimetype="application/json")
            return HttpResponse("Added successfully")
        return HttpResponse("Not an ajax request.")

    except Exception:
        print(Exception)
        print(traceback.format_exc())
        return HttpResponseServerError("An error has occurred while adding a transaction")

def unpack_date(formatted_date, get_end_of_day):
    # assuming d/m/y format
    # print(formatted_date.split("%2F"))
    values = list(map(int, formatted_date.split("/")))
    hours, minutes, seconds, milliseconds = 0, 0, 0, 0
    if get_end_of_day:
        hours, minutes, seconds, milliseconds = 23, 59, 59, 999999
        
    date = datetime(values[2], values[1], values[0], hours, minutes, seconds, milliseconds, get_default_timezone())
    
    # since USE_TZ is true, timezone.now() is recording transactions in
    # UTC, that is, 3 hours ahead of local time. However, admin page displays
    # local times in transaction details.

    return localtime(date, utc)
        
@login_required
def update_tree(request):
    # print balances for given start and end dates
    start_date = unpack_date(request.POST["start_date_formatted"], False)
    end_date = unpack_date(request.POST["end_date_formatted"], True)

    new_balances = get_balance_changes(request.user,
                                       start_date=start_date,
                                       end_date=end_date)
    if request.is_ajax():
        return HttpResponse(json.dumps(new_balances),
                            mimetype="application/json")
    return HttpResponse("error updating tree")

@login_required
def view_transactions(request):
    start_date = unpack_date(request.POST["start_date_formatted"], False)
    end_date = unpack_date(request.POST["end_date_formatted"], True)
    account = Account.objects.get(user=request.user,
                                  short_name__iexact=request.POST["active_account"])
    
    debit_transactions = Transaction.objects.filter(debit=account,
                            date__gte=start_date, date__lte=end_date)
    credit_transactions = Transaction.objects.filter(credit=account,
                            date__gte=start_date, date__lte=end_date)
    raw_transactions = reversed(sorted(chain(debit_transactions,
                                             credit_transactions),
                                       key=lambda tr: tr.date))
    return HttpResponse("<br>".join(map(str, raw_transactions)))

@login_required
def view_latest_transactions(request):
    print("in view_latest_transactions")
    transactions = (Transaction.objects.filter(user=request.user)
                    .order_by("pk").reverse()[:5])
    return HttpResponse("<br>".join(map(str, transactions)))
