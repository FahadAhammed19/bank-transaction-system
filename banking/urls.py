from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
urlpatterns=[
 path('admin/',admin.site.urls),
 path('register/',views.register,name='register'),
 path('login/',auth_views.LoginView.as_view(redirect_authenticated_user=True),name='login'),
 path('logout/',auth_views.LogoutView.as_view(),name='logout'),
 path('',views.dashboard,name='dashboard'),
 path('account/create/',views.create_account,name='create_account'),
 path('deposit/',views.deposit,name='deposit'),
 path('withdraw/',views.withdraw,name='withdraw'),
 path('transactions/',views.history,name='history'),
 path('transactions/export/',views.export_csv,name='export_csv'),
]
