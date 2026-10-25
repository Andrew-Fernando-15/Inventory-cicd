from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db import connection, transaction
from django.contrib import messages
from django.forms import formset_factory
from .models import Product, Invoice, InvoiceItem
from .forms import ProductForm, StockUpdateForm, InvoiceForm, InvoiceItemForm
import uuid


def health_check(request):
    """Health check endpoint required by the CI/CD pipeline."""
    try:
        connection.ensure_connection()
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'service': 'inventory_and_billing'
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)


# --- Product Management ---

def product_list(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'inventory/product_list.html', {'products': products})


def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product.name}' created successfully.")
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Add Product'})


def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Edit Product', 'product': product})


def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' deleted.")
        return redirect('product_list')
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})


# --- Stock Updates ---

def stock_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = StockUpdateForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            qty = form.cleaned_data['quantity']

            if action == 'add':
                product.stock_quantity += qty
            elif action == 'subtract':
                if product.stock_quantity < qty:
                    messages.error(request, f"Cannot subtract {qty}. Current stock is only {product.stock_quantity}.")
                    return render(request, 'inventory/stock_update.html', {'form': form, 'product': product})
                product.stock_quantity -= qty
            elif action == 'set':
                product.stock_quantity = qty

            product.save(update_fields=['stock_quantity'])
            messages.success(request, f"Stock for '{product.name}' updated to {product.stock_quantity}.")
            return redirect('product_list')
    else:
        form = StockUpdateForm()
    return render(request, 'inventory/stock_update.html', {'form': form, 'product': product})


# --- Invoice Generation ---

def invoice_list(request):
    invoices = Invoice.objects.all().order_by('-created_at')
    return render(request, 'inventory/invoice_list.html', {'invoices': invoices})


def invoice_create(request):
    InvoiceItemFormSet = formset_factory(InvoiceItemForm, extra=1, min_num=1, validate_min=True)

    if request.method == 'POST':
        invoice_form = InvoiceForm(request.POST)
        item_formset = InvoiceItemFormSet(request.POST)

        if invoice_form.is_valid() and item_formset.is_valid():
            # Validate stock availability first
            valid = True
            for form in item_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    product = form.cleaned_data['product']
                    qty = form.cleaned_data['quantity']
                    if product.stock_quantity < qty:
                        form.add_error('quantity', f"Insufficient stock for {product.name} (available: {product.stock_quantity})")
                        valid = False

            if valid:
                with transaction.atomic():
                    invoice = invoice_form.save()
                    for form in item_formset:
                        if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                            product = form.cleaned_data['product']
                            qty = form.cleaned_data['quantity']
                            InvoiceItem.objects.create(
                                invoice=invoice,
                                product=product,
                                quantity=qty,
                                unit_price=product.price
                            )
                            # Deduct stock
                            product.stock_quantity -= qty
                            product.save(update_fields=['stock_quantity'])

                    messages.success(request, f"Invoice {invoice.invoice_number} created successfully!")
                    return redirect('invoice_detail', pk=invoice.pk)
    else:
        # Default invoice number
        initial_inv = f"INV-{uuid.uuid4().hex[:6].upper()}"
        invoice_form = InvoiceForm(initial={'invoice_number': initial_inv})
        item_formset = InvoiceItemFormSet()

    return render(request, 'inventory/invoice_create.html', {
        'invoice_form': invoice_form,
        'item_formset': item_formset
    })


def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'inventory/invoice_detail.html', {'invoice': invoice})
