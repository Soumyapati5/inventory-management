from rest_framework import generics, permissions
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Item
from .serializers import ItemSerializer, RegisterSerializer
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# User Registration View
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        logger.info("User registration attempt.")
        return super().create(request, *args, **kwargs)

# Item List and Create View
class ItemListCreateView(generics.ListCreateAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        logger.info("Listing all items.")
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        logger.info("Creating a new item.")
        return super().create(request, *args, **kwargs)

# Item Retrieve, Update, Delete View
class ItemRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        item_id = kwargs.get('pk')
        logger.info(f"Retrieving item with ID: {item_id}")

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
        logger.info(f"Updating item with ID: {item_id}")
        response = super().update(request, *args, **kwargs)
        # Invalidate cache after update
        cache.delete(f'item_{item_id}')
        logger.debug(f"Cache for item {item_id} invalidated.")
        return response

    def destroy(self, request, *args, **kwargs):
        item_id = kwargs.get('pk')
        logger.info(f"Deleting item with ID: {item_id}")
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
