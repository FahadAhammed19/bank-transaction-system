import csv, io, uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Account, Transaction
from .services import record_transaction

class BankingTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(username='alex',password='Test-only-pass-4829')
        self.other=get_user_model().objects.create_user(username='jamie',password='Test-only-pass-4829')
        self.account=Account.objects.create(user=self.user,holder_name='Alex Demo')
        self.other_account=Account.objects.create(user=self.other,holder_name='Jamie Demo')
        self.client.force_login(self.user)
    def post_money(self,path,amount,reference=None,**extra):
        return self.client.post(reverse(path),{'amount':amount,'request_id':reference or uuid.uuid4(),**extra})
    def test_anonymous_pages_are_protected(self):
        self.client.logout()
        for page in ['dashboard','create_account','deposit','withdraw','history','export_csv']:
            self.assertEqual(self.client.get(reverse(page)).status_code,302)
    def test_registration_and_account_creation(self):
        self.client.logout()
        response=self.client.post(reverse('register'),{'first_name':'New Demo','username':'newdemo','password1':'New-demo-password-4829','password2':'New-demo-password-4829'})
        self.assertRedirects(response,reverse('create_account'))
        response=self.client.post(reverse('create_account'),{'holder_name':'New Demo','balance':'9999','user':self.other.pk})
        self.assertRedirects(response,reverse('dashboard'))
        account=Account.objects.get(user__username='newdemo')
        self.assertEqual(account.balance,0)
        self.assertTrue(account.number.startswith('DEMO'))
        self.client.post(reverse('create_account'),{'holder_name':'Duplicate'})
        self.assertEqual(Account.objects.filter(user=account.user).count(),1)
    def test_login_and_post_only_logout(self):
        self.client.logout()
        self.assertEqual(self.client.post(reverse('login'),{'username':'alex','password':'wrong'}).status_code,200)
        self.assertRedirects(self.client.post(reverse('login'),{'username':'alex','password':'Test-only-pass-4829'}),reverse('dashboard'))
        self.assertEqual(self.client.get(reverse('logout')).status_code,405)
        self.assertRedirects(self.client.post(reverse('logout')),reverse('login'))
    def test_deposit_withdraw_and_totals(self):
        self.assertRedirects(self.post_money('deposit','100.25'),reverse('dashboard'))
        self.assertRedirects(self.post_money('withdraw','20.10'),reverse('dashboard'))
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance,Decimal('80.15'))
        self.assertEqual(Transaction.objects.first().balance_after,Decimal('80.15'))
        context=self.client.get(reverse('dashboard')).context
        self.assertEqual(context['deposits'],Decimal('100.25'))
        self.assertEqual(context['withdrawals'],Decimal('20.10'))
        self.assertEqual(context['count'],2)
    def test_invalid_amounts_and_overdraft(self):
        for page in ['deposit','withdraw']:
            for amount in ['0','-1','abc','NaN','1.001','1000000000000']:
                response=self.post_money(page,amount)
                self.assertEqual(response.status_code,200)
                self.assertTrue(response.context['form'].errors)
        self.assertContains(self.post_money('withdraw','1'),'Insufficient balance')
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance,0)
        self.assertFalse(Transaction.objects.exists())
    def test_repeated_form_is_not_applied_twice(self):
        reference=uuid.uuid4()
        self.post_money('deposit','100',reference);self.post_money('deposit','100',reference)
        self.account.refresh_from_db();self.assertEqual(self.account.balance,100)
        self.assertEqual(Transaction.objects.count(),1)
        self.assertEqual(self.post_money('deposit','200',reference).status_code,200)
        self.assertEqual(Transaction.objects.count(),1)
    def test_failed_ledger_insert_rolls_back_balance(self):
        with patch('banking.services.Transaction.objects.create',side_effect=RuntimeError('test')):
            with self.assertRaises(RuntimeError):record_transaction(self.user,'deposit',Decimal('10'),uuid.uuid4())
        self.account.refresh_from_db();self.assertEqual(self.account.balance,0)
    def test_account_ownership_and_no_data_leaks(self):
        record_transaction(self.other,'deposit',Decimal('9876.54'),uuid.uuid4())
        self.assertEqual(self.post_money('deposit','20',account=self.other_account.pk,user=self.other.pk).status_code,302)
        self.other_account.refresh_from_db();self.assertEqual(self.other_account.balance,Decimal('9876.54'))
        for page in ['dashboard','history','export_csv']:
            response=self.client.get(reverse(page),{'account':self.other_account.pk})
            self.assertNotContains(response,'9876.54');self.assertNotContains(response,self.other_account.number)
    def test_history_filter_date_and_csv(self):
        entry,_=record_transaction(self.user,'deposit',Decimal('100'),uuid.uuid4())
        yesterday=timezone.localdate()-timedelta(days=1)
        Transaction.objects.filter(pk=entry.pk).update(created_at=timezone.now()-timedelta(days=1))
        record_transaction(self.user,'withdrawal',Decimal('20'),uuid.uuid4())
        response=self.client.get(reverse('history'),{'kind':'deposit','date':str(yesterday)})
        self.assertEqual(response.context['page_obj'].paginator.count,1)
        response=self.client.get(reverse('export_csv'),{'kind':'deposit','date':str(yesterday)})
        rows=list(csv.reader(io.StringIO(response.content.decode())))
        self.assertEqual(len(rows),2);self.assertEqual(rows[1][0],'Deposit');self.assertEqual(rows[1][1],'100.00')
        self.assertEqual(self.client.get(reverse('export_csv'),{'date':'invalid'}).status_code,400)
    def test_pagination_and_newest_first(self):
        for _ in range(12):record_transaction(self.user,'deposit',Decimal('1'),uuid.uuid4())
        response=self.client.get(reverse('history'))
        self.assertEqual(len(response.context['page_obj']),10)
        self.assertEqual(response.context['page_obj'][0].pk,Transaction.objects.latest('pk').pk)
        self.assertEqual(len(self.client.get(reverse('history'),{'page':2}).context['page_obj']),2)
    def test_balance_cap_and_service_validation(self):
        self.account.balance=Decimal('999999999999.99');self.account.save()
        with self.assertRaises(ValidationError):record_transaction(self.user,'deposit',Decimal('0.01'),uuid.uuid4())
        for amount in ['NaN','Infinity','-1','0','0.001']:
            with self.assertRaises(ValidationError):record_transaction(self.user,'deposit',amount,uuid.uuid4())
        with self.assertRaises(ValidationError):record_transaction(self.user,'invalid','1',uuid.uuid4())
    def test_csrf_and_get_do_not_move_funds(self):
        self.client.get(reverse('deposit'));self.client.get(reverse('withdraw'));self.assertFalse(Transaction.objects.exists())
        client=Client(enforce_csrf_checks=True);client.force_login(self.user)
        self.assertEqual(client.post(reverse('deposit'),{'amount':'100','request_id':uuid.uuid4()}).status_code,403)
    def test_missing_account_redirects_to_setup(self):
        user=get_user_model().objects.create_user(username='empty',password='Test-only-pass-4829')
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse('dashboard')),reverse('create_account'))
