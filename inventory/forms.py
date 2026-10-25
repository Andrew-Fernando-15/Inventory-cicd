from django import forms
from .models import Product, Invoice, InvoiceItem


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'price', 'stock_quantity']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Wireless Mouse'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MOUSE-001'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class StockUpdateForm(forms.Form):
    ACTION_CHOICES = [
        ('add', 'Add Stock (+)'),
        ('subtract', 'Reduce Stock (-)'),
        ('set', 'Set Exact Stock (=)'),
    ]
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantity to adjust'})
    )


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'customer_name', 'notes']
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'INV-1001'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer or Business Name'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Optional customer notes or payment instructions...', 'rows': 2}),
        }


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
        }
