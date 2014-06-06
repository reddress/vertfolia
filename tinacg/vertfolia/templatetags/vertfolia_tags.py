from django import template
from ..models import Account

register = template.Library()

@register.inclusion_tag("vertfolia/children.html")
def display_tree(account, account_balances, is_root):
    children = account.children.all()
    return { 'children': children,
             'account_balances': account_balances,
             'is_root': is_root,
             }
