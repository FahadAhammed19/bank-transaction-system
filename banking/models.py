import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

def account_number():
    return 'DEMO' + uuid.uuid4().hex[:16].upper()

class Account(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='bank_account')
    holder_name=models.CharField(max_length=120)
    number=models.CharField(max_length=20,unique=True,default=account_number,editable=False)
    balance=models.DecimalField(max_digits=14,decimal_places=2,default=Decimal('0.00'),validators=[MinValueValidator(0)])
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.CheckConstraint(condition=models.Q(balance__gte=0),name='account_balance_nonnegative')]
    def __str__(self):
        return f'{self.holder_name} ({self.number})'

class Transaction(models.Model):
    DEPOSIT='deposit'
    WITHDRAWAL='withdrawal'
    TYPES=[(DEPOSIT,'Deposit'),(WITHDRAWAL,'Withdrawal')]
    account=models.ForeignKey(Account,on_delete=models.CASCADE,related_name='transactions')
    kind=models.CharField(max_length=10,choices=TYPES)
    amount=models.DecimalField(max_digits=14,decimal_places=2,validators=[MinValueValidator(Decimal('0.01'))])
    balance_after=models.DecimalField(max_digits=14,decimal_places=2)
    created_at=models.DateTimeField(auto_now_add=True)
    reference=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    class Meta:
        ordering=['-created_at','-id']
        constraints=[models.CheckConstraint(condition=models.Q(amount__gt=0),name='transaction_amount_positive'),models.CheckConstraint(condition=models.Q(balance_after__gte=0),name='transaction_balance_nonnegative'),models.CheckConstraint(condition=models.Q(kind__in=['deposit','withdrawal']),name='valid_transaction_kind')]
