from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from .models import Product, Invoice, InvoiceItem


class HealthCheckTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint(self):
        """Verify that /health/ returns HTTP 200 and healthy JSON payload."""
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('database'), 'connected')


class ProductModelTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Mechanical Keyboard",
            sku="KB-001",
            price=Decimal("79.99"),
            stock_quantity=25
        )

    def test_product_str(self):
        self.assertIn("Mechanical Keyboard", str(self.product))
        self.assertIn("KB-001", str(self.product))

    def test_product_creation(self):
        self.assertEqual(self.product.name, "Mechanical Keyboard")
        self.assertEqual(self.product.price, Decimal("79.99"))
        self.assertEqual(self.product.stock_quantity, 25)


class StockUpdateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(
            name="Gaming Mouse",
            sku="MOUSE-99",
            price=Decimal("49.99"),
            stock_quantity=10
        )

    def test_stock_add(self):
        response = self.client.post(
            reverse('stock_update', args=[self.product.pk]),
            {'action': 'add', 'quantity': 5}
        )
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 15)

    def test_stock_subtract(self):
        response = self.client.post(
            reverse('stock_update', args=[self.product.pk]),
            {'action': 'subtract', 'quantity': 4}
        )
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 6)

    def test_stock_subtract_exceeds_available(self):
        response = self.client.post(
            reverse('stock_update', args=[self.product.pk]),
            {'action': 'subtract', 'quantity': 20}
        )
        # Should stay on page and not reduce stock
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)


class InvoiceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product1 = Product.objects.create(
            name="USB-C Hub",
            sku="HUB-01",
            price=Decimal("25.00"),
            stock_quantity=10
        )
        self.product2 = Product.objects.create(
            name="HDMI Cable",
            sku="CABLE-02",
            price=Decimal("10.00"),
            stock_quantity=20
        )

    def test_invoice_creation_and_stock_deduction(self):
        invoice = Invoice.objects.create(
            invoice_number="INV-TEST-01",
            customer_name="Acme Corp"
        )
        item1 = InvoiceItem.objects.create(
            invoice=invoice,
            product=self.product1,
            quantity=2,
            unit_price=self.product1.price
        )
        item2 = InvoiceItem.objects.create(
            invoice=invoice,
            product=self.product2,
            quantity=3,
            unit_price=self.product2.price
        )

        # Verify line totals
        self.assertEqual(item1.line_total, Decimal("50.00"))
        self.assertEqual(item2.line_total, Decimal("30.00"))

        # Verify invoice total amount
        invoice.refresh_from_db()
        self.assertEqual(invoice.total_amount, Decimal("80.00"))

    def test_invoice_create_view(self):
        payload = {
            'invoice_number': 'INV-VIEW-01',
            'customer_name': 'Jane Doe',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-product': self.product1.pk,
            'form-0-quantity': '3',
        }
        response = self.client.post(reverse('invoice_create'), payload)
        self.assertEqual(response.status_code, 302)

        # Check invoice created
        invoice = Invoice.objects.get(invoice_number='INV-VIEW-01')
        self.assertEqual(invoice.total_amount, Decimal('75.00'))

        # Check stock deducted: 10 - 3 = 7
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock_quantity, 7)


class ProductViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_product_crud_flow(self):
        # Create
        response = self.client.post(reverse('product_create'), {
            'name': 'Ergonomic Chair',
            'sku': 'CHAIR-01',
            'price': '199.99',
            'stock_quantity': '12'
        })
        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(sku='CHAIR-01')
        self.assertEqual(product.name, 'Ergonomic Chair')

        # List
        list_resp = self.client.get(reverse('product_list'))
        self.assertEqual(list_resp.status_code, 200)
        self.assertContains(list_resp, 'Ergonomic Chair')

        # Edit
        edit_resp = self.client.post(reverse('product_edit', args=[product.pk]), {
            'name': 'Ergonomic Chair v2',
            'sku': 'CHAIR-01',
            'price': '229.99',
            'stock_quantity': '15'
        })
        self.assertEqual(edit_resp.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.name, 'Ergonomic Chair v2')
        self.assertEqual(product.price, Decimal('229.99'))

        # Delete
        del_resp = self.client.post(reverse('product_delete', args=[product.pk]))
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(Product.objects.filter(sku='CHAIR-01').exists())
