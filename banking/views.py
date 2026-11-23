import csv
import uuid
from decimal import Decimal
from functools import wraps
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, OperationalError
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from .forms import RegistrationForm, AccountForm, MoneyForm, FilterForm
from .models import Account, Transaction
from .services import record_transaction

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form=RegistrationForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save()
        login(request,user)
        messages.success(request,'Welcome! Create your demo account to get started.')
        return redirect('create_account')
    return render(request,'registration/register.html',{'form':form,'page':'register'})

@login_required
def create_account(request):
    if Account.objects.filter(user=request.user).exists():
        return redirect('dashboard')
    form=AccountForm(request.POST or None,initial={'holder_name':request.user.first_name})
    if request.method=='POST' and form.is_valid():
        account=form.save(commit=False)
        account.user=request.user
        try:
            account.save()
        except IntegrityError:
            if Account.objects.filter(user=request.user).exists():
                return redirect('dashboard')
            form.add_error(None,'Unable to create the account. Please try again.')
        else:
            messages.success(request,'Your demo account is ready. Start with a deposit.')
            return redirect('dashboard')
    return render(request,'account_form.html',{'form':form,'page':'account'})

def account_required(view):
    @login_required
    @wraps(view)
    def wrapped(request,*args,**kwargs):
        try:
            account=Account.objects.get(user=request.user)
        except Account.DoesNotExist:
            return redirect('create_account')
        return view(request,account,*args,**kwargs)
    return wrapped

@account_required
def dashboard(request,account):
    totals=account.transactions.aggregate(deposits=Sum('amount',filter=Q(kind='deposit')),withdrawals=Sum('amount',filter=Q(kind='withdrawal')))
    return render(request,'dashboard.html',{'account':account,'deposits':totals['deposits'] or Decimal('0.00'),'withdrawals':totals['withdrawals'] or Decimal('0.00'),'count':account.transactions.count(),'transactions':account.transactions.all()[:5],'page':'dashboard'})

def money_view(request,account,kind):
    form=MoneyForm(request.POST or None,initial={'request_id':uuid.uuid4()})
    if request.method=='POST' and form.is_valid():
        try:
            entry,created=record_transaction(request.user,kind,form.cleaned_data['amount'],form.cleaned_data['request_id'])
        except ValidationError as exc:
            form.add_error(None,exc)
        except (IntegrityError,OperationalError):
            form.add_error(None,'The account is busy. Please retry this form; duplicate submissions will not be applied twice.')
        else:
            messages.success(request,f'{entry.get_kind_display()} of BDT {entry.amount:,.2f} completed.' if created else 'This transaction was already completed. Your balance was not changed again.')
            return redirect('dashboard')
    account.refresh_from_db()
    return render(request,'money_form.html',{'account':account,'form':form,'kind':kind,'page':kind,'title':'Deposit money' if kind=='deposit' else 'Withdraw money'})

@account_required
def deposit(request,account):
    return money_view(request,account,Transaction.DEPOSIT)

@account_required
def withdraw(request,account):
    return money_view(request,account,Transaction.WITHDRAWAL)

def filtered_transactions(request,account):
    form=FilterForm(request.GET)
    entries=account.transactions.all()
    if form.is_valid():
        if form.cleaned_data['kind']:
            entries=entries.filter(kind=form.cleaned_data['kind'])
        if form.cleaned_data['date']:
            entries=entries.filter(created_at__date=form.cleaned_data['date'])
    else:
        entries=entries.none()
    return form,entries

@account_required
def history(request,account):
    form,entries=filtered_transactions(request,account)
    query=request.GET.copy()
    query.pop('page',None)
    return render(request,'history.html',{'account':account,'form':form,'page_obj':Paginator(entries,10).get_page(request.GET.get('page')),'filter_query':query.urlencode(),'page':'history'})

@account_required
def export_csv(request,account):
    form,entries=filtered_transactions(request,account)
    if not form.is_valid():
        return HttpResponse('Invalid filters. Select a valid type and date.',status=400,content_type='text/plain')
    response=HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition']='attachment; filename="demo-transactions.csv"'
    writer=csv.writer(response)
    writer.writerow(['Type','Amount (BDT)','Date and time (Asia/Dhaka)','Balance after (BDT)','Reference'])
    for entry in entries.iterator():
        writer.writerow([entry.get_kind_display(),format(entry.amount,'.2f'),timezone.localtime(entry.created_at).isoformat(),format(entry.balance_after,'.2f'),str(entry.reference)])
    return response
