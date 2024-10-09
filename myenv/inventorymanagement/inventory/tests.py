# inventory/tests.py

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import Item
from rest_framework_simplejwt.tokens import RefreshToken

class InventoryAPITestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword123',
            email='testuser@example.com'
        )
        # Obtain JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # Set credentials
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        # Create a sample item
        self.item = Item.objects.create(
            name='Sample Item',
            description='This is a sample item.',
            quantity=5,
            price='99.99'
        )

    def test_user_registration(self):
        url = reverse('register')
        data = {
            "username": "newuser",
            "password": "newpassword123",
            "password2": "newpassword123",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(User.objects.get(username='newuser').email, 'newuser@example.com')

    def test_item_creation(self):
        url = reverse('item-list-create')
        data = {
            "name": "New Item",
            "description": "Description for new item.",
            "quantity": 10,
            "price": "150.00"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Item.objects.count(), 2)
        self.assertEqual(Item.objects.get(name='New Item').price, 150.00)

    def test_item_listing(self):
        url = reverse('item-list-create')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_item_retrieval(self):
        url = reverse('item-detail', args=[self.item.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.item.name)

    def test_item_update(self):
        url = reverse('item-detail', args=[self.item.id])
        data = {
            "name": "Updated Item",
            "description": "Updated description.",
            "quantity": 7,
            "price": "89.99"
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, "Updated Item")
        self.assertEqual(self.item.quantity, 7)

    def test_item_deletion(self):
        url = reverse('item-detail', args=[self.item.id])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Item.objects.count(), 0)

    def test_unauthenticated_access(self):
        # Remove authentication credentials
        self.client.credentials()
        url = reverse('item-list-create')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
