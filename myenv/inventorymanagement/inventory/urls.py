from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # API Authentication Endpoints
    path('api/register/', views.RegisterView.as_view(), name='register'),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API Inventory Item Endpoints
    path('api/items/', views.ItemListCreateView.as_view(), name='item-list-create'),
    path('api/items/<int:pk>/', views.ItemRetrieveUpdateDeleteView.as_view(), name='item-detail'),

    # Frontend Authentication Endpoints
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('signin/', views.SignInView.as_view(), name='signin'),
    path('signout/', views.sign_out, name='signout'),

    # Frontend Inventory Management
    path('', views.dashboard, name='dashboard'),  # Dashboard showing inventory items
    path('items/create/', views.create_item, name='create-item'),
    path('items/<int:pk>/edit/', views.edit_item, name='edit-item'),
    path('items/<int:pk>/delete/', views.delete_item, name='delete-item'),
]