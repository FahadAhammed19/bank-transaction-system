from decimal import Decimal
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Account, Transaction

class RegistrationForm(UserCreationForm):
    first_name=forms.CharField(label='Your name',max_length=100)
    class Meta:
        model=User
        fields=['first_name','username','password1','password2']

class AccountForm(forms.ModelForm):
    class Meta:
        model=Account
        fields=['holder_name']
        labels={'holder_name':'Account holder name'}

class MoneyForm(forms.Form):
    amount=forms.DecimalField(label='Amount (BDT)',min_value=Decimal('0.01'),max_value=Decimal('999999999999.99'),max_digits=14,decimal_places=2,widget=forms.NumberInput(attrs={'placeholder':'0.00','step':'0.01','min':'0.01','inputmode':'decimal'}))
    request_id=forms.UUIDField(widget=forms.HiddenInput)

class FilterForm(forms.Form):
    kind=forms.ChoiceField(label='Transaction type',required=False,choices=[('','All transactions')]+Transaction.TYPES)
    date=forms.DateField(label='Date',required=False,widget=forms.DateInput(attrs={'type':'date'}))
