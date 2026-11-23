from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from .models import Account, Transaction

MAX_BALANCE=Decimal('999999999999.99')

@transaction.atomic
def record_transaction(user, kind, amount, reference):
    try:
        amount=Decimal(str(amount))
        valid=amount.is_finite() and amount>0 and amount<=MAX_BALANCE and amount==amount.quantize(Decimal('0.01'))
    except (InvalidOperation,ValueError,TypeError):
        valid=False
    if not valid:
        raise ValidationError('Enter a positive amount with at most two decimal places.')
    if kind not in (Transaction.DEPOSIT,Transaction.WITHDRAWAL):
        raise ValidationError('Invalid transaction type.')
    account=Account.objects.select_for_update().get(user=user)
    existing=Transaction.objects.filter(reference=reference).first()
    if existing:
        if existing.account_id==account.id and existing.kind==kind and existing.amount==amount:
            return existing,False
        raise ValidationError('This form has already been used. Open a fresh form and try again.')
    if kind==Transaction.WITHDRAWAL:
        changed=Account.objects.filter(pk=account.pk,balance__gte=amount).update(balance=F('balance')-amount)
        message='Insufficient balance. Choose an amount within your available balance.'
    else:
        changed=Account.objects.filter(pk=account.pk,balance__lte=MAX_BALANCE-amount).update(balance=F('balance')+amount)
        message='This deposit would exceed the maximum account balance.'
    if not changed:
        raise ValidationError(message)
    account.refresh_from_db(fields=['balance'])
    entry=Transaction.objects.create(account=account,kind=kind,amount=amount,balance_after=account.balance,reference=reference)
    return entry,True
