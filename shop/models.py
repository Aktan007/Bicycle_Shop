from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название роли")
    
    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"
    
    def __str__(self):
        return self.name


class User(models.Model):
    login = models.CharField(max_length=50, unique=True, verbose_name="Логин")
    password = models.CharField(max_length=128, verbose_name="Пароль")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name="Роль")
    full_name = models.CharField(max_length=200, verbose_name="ФИО")
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
    
    def __str__(self):
        return self.full_name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название категории")
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
    
    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="Название поставщика")
    
    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"
    
    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=300, verbose_name="Наименование")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    description = models.TextField(verbose_name="Описание")
    manufacturer = models.CharField(max_length=200, verbose_name="Производитель")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name="Поставщик")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    unit = models.CharField(max_length=20, default="шт", verbose_name="Единица измерения")
    quantity = models.IntegerField(default=0, verbose_name="Количество на складе")
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Скидка %")
    image_path = models.CharField(max_length=500, blank=True, null=True, verbose_name="Путь к изображению")
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
    
    def __str__(self):
        return self.name
    
    @property
    def final_price(self):
        if self.discount > 0:
            return self.price * (1 - self.discount / 100)
        return self.price


class OrderStatus(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название статуса")
    
    class Meta:
        verbose_name = "Статус заказа"
        verbose_name_plural = "Статусы заказов"
    
    def __str__(self):
        return self.name


class Order(models.Model):
    article = models.CharField(max_length=50, unique=True, verbose_name="Артикул")
    status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE, verbose_name="Статус")
    pickup_point = models.CharField(max_length=500, verbose_name="Адрес пункта выдачи")
    order_date = models.DateField(verbose_name="Дата заказа")
    delivery_date = models.DateField(verbose_name="Дата выдачи")
    
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
    
    def __str__(self):
        return f"Заказ {self.article}"
