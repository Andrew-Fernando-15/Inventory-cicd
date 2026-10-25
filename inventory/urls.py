from django.urls import path
from . import views

urlpatterns = [
    # Dashboard / Products
    path('', views.product_list, name='product_list'),
    path('products/', views.product_list, name='product_list_alt'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/<int:pk>/stock/', views.stock_update, name='stock_update'),

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
]
