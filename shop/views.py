import csv
import io

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import User, Role, Product, Category, Supplier, Order, OrderStatus


def login_view(request):
    if request.method == 'POST':
        login = request.POST.get('login')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(login=login, password=password)
            request.session['user_id'] = user.id
            request.session['user_name'] = user.full_name
            request.session['user_role'] = user.role.name
            return redirect('shop:products_list')
        except User.DoesNotExist:
            messages.error(request, 'Неверный логин или пароль')
    
    return render(request, 'shop/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('shop:login')


def products_list(request):
    products = Product.objects.all().select_related('category', 'supplier')

    search = request.GET.get('search', '').strip()
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    discount_filter = request.GET.get('discount', '')
    if discount_filter == 'yes':
        products = products.filter(discount__gt=0)
    elif discount_filter == 'no':
        products = products.filter(discount=0)
    elif discount_filter == 'high':
        products = products.filter(discount__gte=15)

    price_sort = request.GET.get('price', '')
    if price_sort == 'asc':
        products = products.order_by('price')
    elif price_sort == 'desc':
        products = products.order_by('-price')

    qty_filter = request.GET.get('qty', '')
    if qty_filter == 'in_stock':
        products = products.filter(quantity__gt=0)
    elif qty_filter == 'out':
        products = products.filter(quantity=0)

    user_role = request.session.get('user_role', 'Гость')
    user_name = request.session.get('user_name', '')

    context = {
        'products': products,
        'user_role': user_role,
        'user_name': user_name,
        'search': search,
        'discount_filter': discount_filter,
        'price_sort': price_sort,
        'qty_filter': qty_filter,
    }
    return render(request, 'shop/products_list.html', context)


def profile_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('shop:login')

    user = User.objects.select_related('role').get(id=user_id)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if full_name:
            user.full_name = full_name
            request.session['user_name'] = full_name

        if new_password:
            if new_password == confirm_password:
                user.password = new_password
                messages.success(request, 'Пароль успешно изменён')
            else:
                messages.error(request, 'Пароли не совпадают')
                return render(request, 'shop/profile.html', {
                    'profile_user': user,
                    'user_name': request.session.get('user_name', ''),
                    'user_role': request.session.get('user_role', ''),
                })

        user.save()
        messages.success(request, 'Профиль обновлён')
        return redirect('shop:profile')

    context = {
        'profile_user': user,
        'user_name': request.session.get('user_name', ''),
        'user_role': request.session.get('user_role', ''),
    }
    return render(request, 'shop/profile.html', context)


def product_edit(request, pk):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('shop:login')

    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get('name', '').strip()
        product.description = request.POST.get('description', '').strip()
        product.manufacturer = request.POST.get('manufacturer', '').strip()
        product.price = request.POST.get('price', 0)
        product.discount = request.POST.get('discount', 0)
        product.quantity = request.POST.get('quantity', 0)
        product.unit = request.POST.get('unit', 'шт').strip()

        category_id = request.POST.get('category')
        supplier_id = request.POST.get('supplier')
        if category_id:
            product.category_id = category_id
        if supplier_id:
            product.supplier_id = supplier_id

        if request.FILES.get('image'):
            image = request.FILES['image']
            import os
            from django.conf import settings
            filename = image.name
            path = os.path.join(settings.MEDIA_ROOT, 'products', filename)
            with open(path, 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)
            product.image_path = filename

        product.save()
        messages.success(request, f'Товар «{product.name}» обновлён')
        return redirect('shop:products_list')

    context = {
        'product': product,
        'categories': categories,
        'suppliers': suppliers,
        'user_name': request.session.get('user_name', ''),
        'user_role': request.session.get('user_role', ''),
    }
    return render(request, 'shop/product_edit.html', context)


def _parse_uploaded_file(uploaded_file):
    """Return list of rows (as lists) from a CSV or XLSX upload. First row is headers."""
    name = uploaded_file.name.lower()
    if name.endswith('.xlsx'):
        import openpyxl
        wb = openpyxl.load_workbook(uploaded_file)
        ws = wb.active
        rows = [[str(c) if c is not None else '' for c in row]
                for row in ws.iter_rows(values_only=True)]
        return rows
    else:
        raw = uploaded_file.read()
        for enc in ('utf-8-sig', 'utf-8', 'cp1251'):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        reader = csv.reader(io.StringIO(text), delimiter=';')
        return list(reader)


def import_documents(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('shop:login')

    context = {
        'user_name': request.session.get('user_name', ''),
        'user_role': request.session.get('user_role', ''),
        'result': None,
    }

    if request.method == 'POST':
        uploaded = request.FILES.get('document')
        if not uploaded:
            messages.error(request, 'Файл не выбран')
            return render(request, 'shop/import.html', context)

        ext = uploaded.name.rsplit('.', 1)[-1].lower()
        if ext not in ('csv', 'xlsx'):
            messages.error(request, 'Поддерживаются только форматы CSV и XLSX')
            return render(request, 'shop/import.html', context)

        try:
            rows = _parse_uploaded_file(uploaded)
        except Exception as e:
            messages.error(request, f'Ошибка чтения файла: {e}')
            return render(request, 'shop/import.html', context)

        if len(rows) < 2:
            messages.error(request, 'Файл пуст или содержит только заголовок')
            return render(request, 'shop/import.html', context)

        header = [h.strip().lower() for h in rows[0]]
        doc_type = request.POST.get('doc_type', 'auto')

        if doc_type == 'auto':
            if any('наименование' in h for h in header):
                doc_type = 'products'
            elif any('логин' in h for h in header):
                doc_type = 'users'
            elif any('артикул' in h or 'заказ' in h for h in header):
                doc_type = 'orders'
            else:
                messages.error(request, 'Не удалось определить тип документа. Выберите тип вручную.')
                context['rows_preview'] = rows[:4]
                return render(request, 'shop/import.html', context)

        count = 0
        from datetime import date, datetime

        def safe_date(value):
            if not value or not str(value).strip():
                return date.today()
            value = str(value).strip().split(' ')[0]
            for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y'):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            return date.today()

        if doc_type == 'products':
            for row in rows[1:]:
                if len(row) < 9 or not (row[1] if len(row) > 1 else '').strip():
                    continue
                name = row[1].strip()
                unit = row[2].strip().rstrip('.') or 'шт'
                try:
                    price = float(str(row[3]).replace(',', '.')) if row[3] else 0
                except ValueError:
                    price = 0
                supplier_name = row[4].strip() or 'Неизвестный'
                manufacturer = row[5].strip()
                category_name = row[6].strip() or 'Без категории'
                try:
                    discount = float(str(row[7]).replace(',', '.')) if row[7] else 0
                except ValueError:
                    discount = 0
                try:
                    quantity = int(float(str(row[8]))) if row[8] else 0
                except ValueError:
                    quantity = 0
                description = row[9].strip() if len(row) > 9 else ''
                photo = row[10].strip() if len(row) > 10 else ''

                category, _ = Category.objects.get_or_create(name=category_name)
                supplier, _ = Supplier.objects.get_or_create(name=supplier_name)
                _, created = Product.objects.get_or_create(
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
                if created:
                    count += 1
            messages.success(request, f'Товары импортированы: добавлено {count} новых записей')

        elif doc_type == 'users':
            for row in rows[1:]:
                if len(row) < 4 or not row[2].strip():
                    continue
                role_name, full_name, login, password = row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip()
                role, _ = Role.objects.get_or_create(name=role_name or 'Сотрудник')
                _, created = User.objects.get_or_create(
                    login=login,
                    defaults={'password': password, 'role': role, 'full_name': full_name},
                )
                if created:
                    count += 1
            messages.success(request, f'Пользователи импортированы: добавлено {count} новых записей')

        elif doc_type == 'orders':
            for row in rows[1:]:
                if len(row) < 5 or not row[0].strip():
                    continue
                order_num = row[0].strip()
                order_date = safe_date(row[2] if len(row) > 2 else '')
                delivery_date = safe_date(row[3] if len(row) > 3 else '')
                pickup = row[4].strip() if len(row) > 4 else ''
                status_name = row[7].strip() if len(row) > 7 else 'Новый'
                status, _ = OrderStatus.objects.get_or_create(name=status_name or 'Новый')
                _, created = Order.objects.get_or_create(
                    article=order_num,
                    defaults={
                        'status': status,
                        'pickup_point': pickup,
                        'order_date': order_date,
                        'delivery_date': delivery_date,
                    },
                )
                if created:
                    count += 1
            messages.success(request, f'Заказы импортированы: добавлено {count} новых записей')

        return redirect('shop:import_documents')

    return render(request, 'shop/import.html', context)
