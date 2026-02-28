from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('products/', views.products_list, name='products_list'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('profile/', views.profile_view, name='profile'),
    path('import/', views.import_documents, name='import_documents'),
]
