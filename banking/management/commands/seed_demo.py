from datetime import timedelta
from decimal import Decimal
import uuid
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from banking.models import Account, Transaction
from banking.services import record_transaction

class Command(BaseCommand):
    help='Create fictional demo users and transactions in an empty demo setup.'
    @transaction.atomic
    def handle(self,*args,**options):
        User=get_user_model()
        if User.objects.filter(username__in=['demo','demo_other']).exists():
            raise CommandError('Demo users already exist; existing data has not been changed.')
        user=User.objects.create_user(username='demo',first_name='Alex Morgan',password='DemoPass!2026')
        Account.objects.create(user=user,holder_name='Alex Morgan',number='DEMO0000000000000001')
        other=User.objects.create_user(username='demo_other',first_name='Jamie Taylor',password='DemoPass!2026')
        Account.objects.create(user=other,holder_name='Jamie Taylor',number='DEMO0000000000000002')
        values=[('deposit','25000'),('withdrawal','1250'),('deposit','8000'),('withdrawal','2400'),('deposit','4500'),('withdrawal','650'),('withdrawal','1000'),('deposit','12000'),('withdrawal','3600'),('deposit','2500'),('withdrawal','900'),('withdrawal','1200'),('deposit','6000'),('withdrawal','1800')]
        for i,(kind,amount) in enumerate(values):
            entry,_=record_transaction(user,kind,Decimal(amount),uuid.uuid4())
            Transaction.objects.filter(pk=entry.pk).update(created_at=timezone.now()-timedelta(days=len(values)-i,hours=i%4))
        record_transaction(other,'deposit',Decimal('1500'),uuid.uuid4())
        self.stdout.write(self.style.SUCCESS('Created demo and demo_other. Password: DemoPass!2026. Fictional data only.'))
