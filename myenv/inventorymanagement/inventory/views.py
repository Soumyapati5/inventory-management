from rest_framework import generics, permissions
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, ItemSerializer
from .models import Item
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.views import View
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Initialize logger
logger = logging.getLogger(__name__)

# User Registration API View
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        logger.info(f"New user registered: {user.username}")

# User Registration Frontend View (if integrating frontend)
class SignUpView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'signup.html', {'form': form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            logger.info(f"New user registered via frontend: {user.username}")
            return redirect('dashboard')
        else:
            return render(request, 'signup.html', {'form': form})

# User Login Frontend View
class SignInView(View):
    def get(self, request):
        form = AuthenticationForm()
        return render(request, 'signin.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            logger.info(f"User logged in via frontend: {user.username}")
            return redirect('dashboard')
        else:
            return render(request, 'signin.html', {'form': form})

# User Logout Frontend View
def sign_out(request):
    logout(request)
    logger.info("User logged out via frontend.")
    return redirect('signin')

# Inventory Item API Views
class ItemListCreateView(generics.ListCreateAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        logger.info("Listing all inventory items via API.")
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        logger.info("Creating a new inventory item via API.")
        return super().create(request, *args, **kwargs)

class ItemRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        item_id = kwargs.get('pk')
        logger.info(f"Retrieving inventory item with ID: {item_id}")

        # Check Redis cache first
        cached_item = cache.get(f'item_{item_id}')
        if cached_item:
            logger.debug(f"Item {item_id} fetched from cache.")
            return Response(cached_item)

        # If not in cache, fetch from DB
        response = super().retrieve(request, *args, **kwargs)
        # Cache the item data
        cache.set(f'item_{item_id}', response.data, timeout=60*5)  # Cache for 5 minutes
        logger.debug(f"Item {item_id} cached.")
        return response

    def update(self, request, *args, **kwargs):
        item_id = kwargs.get('pk')
        logger.info(f"Updating inventory item with ID: {item_id}")
        response = super().update(request, *args, **kwargs)
        # Invalidate cache after update
        cache.delete(f'item_{item_id}')
        logger.debug(f"Cache for item {item_id} invalidated.")
        return response

    def destroy(self, request, *args, **kwargs):
        item_id = kwargs.get('pk')
        logger.info(f"Deleting inventory item with ID: {item_id}")
        response = super().destroy(request, *args, **kwargs)
        # Invalidate cache after deletion
        cache.delete(f'item_{item_id}')
        logger.debug(f"Cache for item {item_id} invalidated.")
        return response

# Root API View
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_root(request):
    return JsonResponse({
        'message': 'Welcome to the Inventory Management API!',
        'endpoints': {
            'register': '/api/register/',
            'login': '/api/login/',
            'token_refresh': '/api/token/refresh/',
            'items': '/api/items/',
        }
    })

# Frontend Dashboard View
@login_required
def dashboard(request):
    items = Item.objects.all()
    return render(request, 'dashboard.html', {'items': items})

# Frontend Create Item View
@login_required
def create_item(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        quantity = request.POST.get('quantity', 0)
        price = request.POST.get('price', 0.0)

        # Simple validation
        if Item.objects.filter(name=name).exists():
            messages.error(request, "Item already exists.")
            return redirect('create-item')

        Item.objects.create(
            name=name,
            description=description,
            quantity=quantity,
            price=price
        )
        logger.info(f"Item created via frontend: {name}")
        return redirect('dashboard')
    return render(request, 'create_item.html')

# Frontend Edit Item View
@login_required
def edit_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        item.name = request.POST.get('name')
        item.description = request.POST.get('description', '')
        item.quantity = request.POST.get('quantity', 0)
        item.price = request.POST.get('price', 0.0)
        item.save()
        messages.success(request, "Item updated successfully.")
        logger.info(f"Item updated via frontend: {item.name}")
        return redirect('dashboard')
    return render(request, 'edit_item.html', {'item': item})

# Frontend Delete Item View
@login_required
def delete_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        logger.info(f"Item deleted via frontend: {item.name}")
        item.delete()
        messages.success(request, "Item deleted successfully.")
        return redirect('dashboard')
    return render(request, 'delete_item.html', {'item': item})
