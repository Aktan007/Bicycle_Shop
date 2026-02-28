import csv
import glob
import os
from datetime import datetime, date

from django.core.management.base import BaseCommand

from shop.models import (
    Role, User, Category, Supplier, Product,
    OrderStatus, Order,
)


class Command(BaseCommand):
    help = 'Импорт данных из csv файлов в базу данных'

    def handle(self, *args, **options):
        self.import_users()
        self.import_products()
        self.import_orders()
        self.stdout.write(self.style.SUCCESS('Импорт завершён успешно!'))

    @staticmethod
    def _read_csv(path):
        with open(path, encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')
            rows = list(reader)
        return rows[0], rows[1:]

    def import_users(self):
        path = os.path.join('docs', 'user_import.csv')
        header, rows = self._read_csv(path)

        count = 0
        for row in rows:
            if len(row) < 4 or not row[0].strip():
                continue
            role_name, full_name, login, password = row[:4]

            role, _ = Role.objects.get_or_create(name=role_name.strip())
            User.objects.get_or_create(
                login=login.strip(),
                defaults={
                    'password': password.strip(),
                    'role': role,
                    'full_name': full_name.strip(),
                },
            )
            count += 1

        self.stdout.write(f'  Пользователи: {count} записей')

    def import_products(self):
        path = os.path.join('docs', 'Tovar.csv')
        header, rows = self._read_csv(path)

        count = 0
        for row in rows:
            if len(row) < 11 or not row[1].strip():
                continue

            article = row[0].strip()
            name = row[1].strip()
            unit = row[2].strip().rstrip('.') or 'шт'
            price = float(row[3]) if row[3] else 0
            supplier_name = row[4].strip() or 'Неизвестный'
            manufacturer = row[5].strip()
            category_name = row[6].strip() or 'Без категории'
            discount = float(row[7]) if row[7] else 0
            quantity = int(row[8]) if row[8] else 0
            description = row[9].strip() if len(row) > 9 else ''
            photo = row[10].strip() if len(row) > 10 else ''

            category, _ = Category.objects.get_or_create(name=category_name)
            supplier, _ = Supplier.objects.get_or_create(name=supplier_name)

            Product.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'description': description,
                    'manufacturer': manufacturer,
                    'supplier': supplier,
                    'price': price,
                    'unit': unit,
                    'quantity': quantity,
                    'discount': discount,
                    'image_path': photo,
                },
            )
            count += 1

        self.stdout.write(f'  Товары: {count} записей')

    def import_orders(self):
        order_files = [f for f in glob.glob('docs/*.csv')
                       if 'Tovar' not in f and 'user' not in f
                       and 'import' in f.lower() and 'ункт' not in f]
        if not order_files:
            self.stdout.write('  Файл заказов не найден')
            return

        pickup_files = [f for f in glob.glob('docs/*.csv') if 'ункт' in f]
        pickup_points = {}
        if pickup_files:
            with open(pickup_files[0], encoding='utf-8-sig') as f:
                for idx, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        pickup_points[idx] = line

        header, rows = self._read_csv(order_files[0])

        count = 0
        for row in rows:
            if len(row) < 8 or not row[0].strip():
                continue

            order_num = row[0].strip()
            article = row[1].strip()
            order_date_str = row[2].strip()
            delivery_date_str = row[3].strip()
            pickup_id = row[4].strip()
            client_name = row[5].strip()
            code = row[6].strip()
            status_name = row[7].strip() or 'Новый'

            status, _ = OrderStatus.objects.get_or_create(name=status_name)

            try:
                pickup_address = pickup_points.get(int(pickup_id), pickup_id)
            except (ValueError, TypeError):
                pickup_address = pickup_id

            order_date = self._safe_date(order_date_str)
            delivery_date = self._safe_date(delivery_date_str)

            Order.objects.get_or_create(
                article=order_num,
                defaults={
                    'status': status,
                    'pickup_point': pickup_address,
                    'order_date': order_date,
                    'delivery_date': delivery_date,
                },
            )
            count += 1

        self.stdout.write(f'  Заказы: {count} записей')

    @staticmethod
    def _safe_date(value):
        if isinstance(value, (datetime, date)):
            return value if isinstance(value, date) else value.date()
        if not value or not str(value).strip():
            return date.today()
        value = str(value).strip()
        if ' ' in value:
            value = value.split(' ')[0]
        for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y'):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        parts = value.replace('-', '.').replace('/', '.').split('.')
        if len(parts) == 3:
            try:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                if y > 31:
                    pass
                else:
                    d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                if d > 28 and m == 2:
                    d = 28
                return date(y, m, d)
            except (ValueError, TypeError):
                pass
        return date.today()
