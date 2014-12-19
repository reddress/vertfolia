import traceback
import json
from datetime import datetime, timedelta
from itertools import chain

from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseServerError
from django.template import RequestContext
from django.utils import timezone
from django.utils.timezone import get_default_timezone, localtime, utc
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .models import Account, Currency, Transaction
from .models import get_balance_changes
from .models import get_balance_changes, get_children_accounts
from .models import is_parent

LATEST_COUNT = 15

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
                           .order_by("pk").reverse()[:LATEST_COUNT])
    
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
        hour_minute_second = list(map(int, request.POST["time"].split(":")))

        add_date = localtime(datetime(*(year_month_day+hour_minute_second),
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

def format_transaction(transaction):
    date_format = "%a %d/%m/%y"
    fmt_string = "%s %s %.2f %s/%s %s\n"
        
    return (fmt_string %
        (localtime(transaction.date.replace(tzinfo=utc)).strftime(date_format),
         transaction.currency.short_name,
         transaction.value,
         transaction.debit, transaction.credit,
         transaction.description,))

def format_transaction_short(transaction):
    fmt_string = "%s %.2f %s/%s %s\n"
        
    return (fmt_string %
        (transaction.currency.short_name,
         transaction.value,
         transaction.debit, transaction.credit,
         transaction.description,))
    
@login_required
def view_transactions(request):
    start_date = unpack_date(request.POST["start_date_formatted"], False)
    end_date = unpack_date(request.POST["end_date_formatted"], True)
    account = Account.objects.get(user=request.user,
                                  short_name__iexact=request.POST["active_account"])
    
    account_list = [account]

    try:
        if request.POST["include_children"] == "on":
            account_list = account_list + get_children_accounts(account)
    except:
        pass  # checkbox unchecked

    # debit_transactions = Transaction.objects.filter(debit__in=account_list,
    #                        date__gte=start_date, date__lte=end_date)
    # credit_transactions = Transaction.objects.filter(credit__in=account_list,
    #                        date__gte=start_date, date__lte=end_date)
    # raw_transactions = reversed(sorted(set(chain(debit_transactions,
    #                                        credit_transactions)),
    #                                   key=lambda tr: tr.date))

    transactions = Transaction.objects.filter(Q(debit__in=account_list) | Q(credit__in=account_list), date__gte=start_date, date__lte=end_date).order_by("-date").select_related('currency', 'debit', 'credit')

    debit_total = 0
    credit_total = 0

    account_children = [account] + get_children_accounts(account)
    
    account_short_name = account.short_name
    for transaction in transactions:
        # if transaction.debit.short_name == account_short_name:
        if transaction.debit in account_children:
            debit_total += transaction.value
        # if transaction.credit.short_name == account_short_name:
        if transaction.credit in account_children:
            credit_total += transaction.value
            
    # return HttpResponse(map(format_transaction, raw_transactions))
    return render_to_response("vertfolia/transactions_table.html",
                              { 'transactions': transactions,
                                'account_name': account_short_name,
                                'debit_total': debit_total,
                                'credit_total': credit_total, })

@login_required
def view_latest_transactions(request):
    # print("in view_latest_transactions")
    transactions = (Transaction.objects.filter(user=request.user)
                    .order_by("pk").reverse()[:LATEST_COUNT])
    return HttpResponse("<br>".join(map(str, transactions)))

@login_required
def view_daily_expenses(request):
    start_date = unpack_date(request.POST["start_date_formatted"], False)
    end_date = unpack_date(request.POST["end_date_formatted"], True)
    end_date_count = unpack_date(request.POST["end_date_formatted"], False)
    expense_account = Account.objects.get(user=request.user,
                                          short_name="Expense")
    account_list = ([expense_account] +
                    get_children_accounts(expense_account))

    raw_transactions = Transaction.objects.filter(debit__in=account_list,
                            date__gte=start_date, date__lte=end_date).distinct()
    
    daily_totals = {}
    daily_header = {}
    daily_transactions = {}
    days_list = []

    # delta_days = (end_date_count-start_date).days + 1
    delta_days = (datetime.strptime(request.POST["end_date_formatted"], "%d/%m/%Y") - datetime.strptime(request.POST["start_date_formatted"], "%d/%m/%Y")).days + 1
    for n in range(delta_days):
        day = (start_date + timedelta(n)).strftime("%Y-%m-%d")
        days_list.append(day)
        daily_totals[day] = 0
        daily_transactions[day] = []

    for transaction in raw_transactions:
        date_key = localtime(transaction.date.replace(tzinfo=utc)).strftime("%Y-%m-%d")

        # if date_key not in daily_totals:
            # days_list.append(date_key)
            # daily_totals[date_key] = 0
            # daily_transactions[date_key] = []
        # else:
        daily_totals[date_key] += transaction.value
        daily_transactions[date_key].append("    " + format_transaction_short(transaction))

    for day in sorted(days_list):
        daily_header[day] = "%s %.2f" % (datetime.strptime(day, "%Y-%m-%d").strftime("%a %d/%m/%y"), daily_totals[day])
        
    return render_to_response("vertfolia/daily_expenses_table.html",
                              { 'days': days_list[::-1],
                                'daily_header': daily_header,
                                'daily_totals': daily_totals,
                                'daily_transactions': daily_transactions, })
    

@login_required
def search(request):
    transactions = Transaction.objects.filter(user=request.user, description__icontains=request.POST["search_parameter"]).order_by("-date")

    debit_total = 0
    credit_total = 0
    search_total = 0

    for transaction in transactions:
        search_total += transaction.value

    currency = "" if not transactions else transactions[0].currency.short_name

    return render_to_response("vertfolia/transactions_table.html",
                              { 'transactions': transactions,
                                'account_name': 'SEARCH',
                                'debit_total': debit_total,
                                'credit_total': credit_total,
                                'search_total': search_total,
                                'search_currency': currency, })
