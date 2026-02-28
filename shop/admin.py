from django.contrib import admin
from .models import Role, User, Category, Supplier, Product, OrderStatus, Order


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'login', 'full_name', 'role')
    list_filter = ('role',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'manufacturer', 'price', 'discount', 'quantity')
    list_filter = ('category', 'supplier', 'manufacturer')
    search_fields = ('name', 'description', 'manufacturer')


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'article', 'status', 'order_date', 'delivery_date')
    list_filter = ('status',)
