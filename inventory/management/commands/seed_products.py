from decimal import Decimal
from django.core.management.base import BaseCommand
from inventory.models import Product


class Command(BaseCommand):
    help = 'Seeds 15 realistic inventory products with varied stock levels.'

    def handle(self, *args, **options):
        products_data = [
            {
                'name': 'Dell PowerEdge R750 Rack Server',
                'sku': 'SRV-DELL-750',
                'price': Decimal('2499.00'),
                'stock_quantity': 15,
            },
            {
                'name': 'Cisco Catalyst 9300 48-Port Switch',
                'sku': 'NET-CSCO-9300',
                'price': Decimal('1850.00'),
                'stock_quantity': 8,
            },
            {
                'name': 'Ubiquiti UniFi Pro Wi-Fi 6 AP',
                'sku': 'WIFI-UBNT-U6P',
                'price': Decimal('179.00'),
                'stock_quantity': 45,
            },
            {
                'name': 'Fortinet FortiGate 60F Firewall',
                'sku': 'SEC-FORTI-60F',
                'price': Decimal('520.00'),
                'stock_quantity': 0,
            },
            {
                'name': 'Samsung 990 Pro 2TB NVMe SSD',
                'sku': 'STR-SAM-990P',
                'price': Decimal('169.50'),
                'stock_quantity': 60,
            },
            {
                'name': 'Seagate Exos 16TB Enterprise HDD',
                'sku': 'STR-SEAG-16TB',
                'price': Decimal('285.00'),
                'stock_quantity': 24,
            },
            {
                'name': 'APC Smart-UPS 1500VA LCD 230V',
                'sku': 'PWR-APC-1500',
                'price': Decimal('649.00'),
                'stock_quantity': 5,
            },
            {
                'name': 'Logitech MX Master 3S Wireless Mouse',
                'sku': 'ACC-LOGI-MX3S',
                'price': Decimal('99.00'),
                'stock_quantity': 35,
            },
            {
                'name': 'Keychron K2 Mechanical Keyboard',
                'sku': 'ACC-KEYC-K2',
                'price': Decimal('89.99'),
                'stock_quantity': 20,
            },
            {
                'name': 'Dell UltraSharp 27 4K Monitor',
                'sku': 'DISP-DELL-U27',
                'price': Decimal('499.00'),
                'stock_quantity': 7,
            },
            {
                'name': 'Synology DiskStation DS923+ 4-Bay NAS',
                'sku': 'NAS-SYNO-923',
                'price': Decimal('599.00'),
                'stock_quantity': 12,
            },
            {
                'name': 'MikroTik Cloud Router Switch 326',
                'sku': 'NET-MIKR-326',
                'price': Decimal('199.00'),
                'stock_quantity': 0,
            },
            {
                'name': 'StarTech 42U Server Rack Cabinet',
                'sku': 'RCK-STAR-42U',
                'price': Decimal('1150.00'),
                'stock_quantity': 3,
            },
            {
                'name': 'Cat6A Shielded Ethernet Cable 1000ft',
                'sku': 'CBL-CAT6A-1K',
                'price': Decimal('185.00'),
                'stock_quantity': 50,
            },
            {
                'name': 'YubiKey 5 NFC Hardware Security Key',
                'sku': 'SEC-YUBI-5NFC',
                'price': Decimal('55.00'),
                'stock_quantity': 80,
            },
        ]

        created_count = 0
        updated_count = 0

        for item in products_data:
            obj, created = Product.objects.update_or_create(
                sku=item['sku'],
                defaults={
                    'name': item['name'],
                    'price': item['price'],
                    'stock_quantity': item['stock_quantity'],
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed complete: {created_count} products created, {updated_count} updated. '
                f'Total products in database: {Product.objects.count()}'
            )
        )
