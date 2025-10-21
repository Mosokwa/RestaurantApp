from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from ..models import Customer, RestaurantStaff
from ..serializers import (
    UserProfileSerializer,
    CustomerSerializer, RestaurantStaffSerializer, StaffCreateSerializer
)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

class CustomerListView(generics.ListAPIView):
    queryset = Customer.objects.select_related('user')
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAdminUser]

class CustomerDetailView(generics.RetrieveUpdateAPIView):
    queryset = Customer.objects.select_related('user')
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Customers can only view their own profile
        if self.request.user.user_type == 'customer':
            return get_object_or_404(Customer, user=self.request.user)
        # Admins can view any customer
        return super().get_object()

class RestaurantStaffListView(generics.ListCreateAPIView):
    serializer_class = RestaurantStaffSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'admin':
            return RestaurantStaff.objects.select_related('user', 'restaurant')
        elif user.user_type == 'owner':
            # Owners can see staff from their restaurants
            return RestaurantStaff.objects.filter(
                restaurant__owner=user
            ).select_related('user', 'restaurant')
        elif user.user_type == 'staff':
            # Staff can see other staff from same restaurant
            staff_profile = user.staff_profile
            return RestaurantStaff.objects.filter(
                restaurant=staff_profile.restaurant
            ).select_related('user', 'restaurant')
        
        return RestaurantStaff.objects.none()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StaffCreateSerializer
        return RestaurantStaffSerializer

class RestaurantStaffDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RestaurantStaffSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'admin':
            return RestaurantStaff.objects.select_related('user', 'restaurant')
        elif user.user_type == 'owner':
            return RestaurantStaff.objects.filter(restaurant__owner=user)
        elif user.user_type == 'staff':
            staff_profile = user.staff_profile
            return RestaurantStaff.objects.filter(restaurant=staff_profile.restaurant)
        
        return RestaurantStaff.objects.none()

class MyStaffProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = RestaurantStaffSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        if self.request.user.user_type != 'staff':
            raise PermissionDenied("Only staff members can access this endpoint")
        return get_object_or_404(RestaurantStaff, user=self.request.user)