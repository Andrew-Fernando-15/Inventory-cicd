from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from inventory.models import Product, Invoice, InvoiceItem


class Command(BaseCommand):
    help = 'Seeds 5 realistic multi-item customer invoices.'

    def handle(self, *args, **options):
        invoices_data = [
            {
                'invoice_number': 'INV-2026-001',
                'customer_name': 'Apex Tech Solutions Ltd',
                'notes': 'Deliver to Data Center 2, Rack 14. Priority express delivery.',
                'items': [
                    {'sku': 'SRV-DELL-750', 'quantity': 1},
                    {'sku': 'STR-SAM-990P', 'quantity': 2},
                ],
            },
            {
                'invoice_number': 'INV-2026-002',
                'customer_name': 'Quantum Cloud Networks',
                'notes': 'Net 30 payment terms agreed. Installation support requested.',
                'items': [
                    {'sku': 'NET-CSCO-9300', 'quantity': 1},
                    {'sku': 'CBL-CAT6A-1K', 'quantity': 2},
                ],
            },
            {
                'invoice_number': 'INV-2026-003',
                'customer_name': 'Nexus Cyber Security Inc',
                'notes': 'Hardware security tokens for internal developer access control.',
                'items': [
                    {'sku': 'SEC-YUBI-5NFC', 'quantity': 10},
                    {'sku': 'ACC-LOGI-MX3S', 'quantity': 2},
                ],
            },
            {
                'invoice_number': 'INV-2026-004',
                'customer_name': 'Horizon Media Group',
                'notes': 'Video editing studio expansion. Handle monitors with fragile care.',
                'items': [
                    {'sku': 'DISP-DELL-U27', 'quantity': 2},
                    {'sku': 'NAS-SYNO-923', 'quantity': 1},
                    {'sku': 'STR-SEAG-16TB', 'quantity': 2},
                ],
            },
            {
                'invoice_number': 'INV-2026-005',
                'customer_name': 'Vanguard University IT Dept',
                'notes': 'Campus Wi-Fi upgrade Phase 1. Delivery to Main Admin Building.',
                'items': [
                    {'sku': 'WIFI-UBNT-U6P', 'quantity': 5},
                    {'sku': 'PWR-APC-1500', 'quantity': 1},
                ],
            },
        ]

        created_count = 0
        with transaction.atomic():
            for data in invoices_data:
                invoice, created = Invoice.objects.get_or_create(
                    invoice_number=data['invoice_number'],
                    defaults={
                        'customer_name': data['customer_name'],
                        'notes': data['notes'],
                    }
                )

                if created:
                    created_count += 1
                    for item_data in data['items']:
                        product = Product.objects.get(sku=item_data['sku'])
                        qty = item_data['quantity']

                        InvoiceItem.objects.create(
                            invoice=invoice,
                            product=product,
                            quantity=qty,
                            unit_price=product.price
                        )

                        # Deduct warehouse stock
                        if product.stock_quantity >= qty:
                            product.stock_quantity -= qty
                            product.save(update_fields=['stock_quantity'])

                    invoice.update_total()

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed complete: {created_count} invoices created. '
                f'Total invoices in database: {Invoice.objects.count()}'
            )
        )
