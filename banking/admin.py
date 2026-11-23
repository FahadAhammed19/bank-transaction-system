from django.contrib import admin
from .models import Account, Transaction

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display=['holder_name','number','balance']
    readonly_fields=['user','holder_name','number','balance','created_at']
    def has_add_permission(self,request):return False
    def has_delete_permission(self,request,obj=None):return False

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display=['account','kind','amount','balance_after','created_at']
    readonly_fields=['account','kind','amount','balance_after','created_at','reference']
    def has_add_permission(self,request):return False
    def has_delete_permission(self,request,obj=None):return False
