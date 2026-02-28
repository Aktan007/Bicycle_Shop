from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import User, Product, Category, Supplier


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
