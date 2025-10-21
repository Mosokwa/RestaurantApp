from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from ..models import User, Customer, RestaurantStaff

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
            if data['password'] != data['password_confirm']:
                raise ValidationError("passwords don't match")
            if User.objects.filter(email=data['email']).exists():
                raise ValidationError("A user with this email already exists.")
            return data
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise ValidationError("A user with this email already exists.")
        return value.lower()
    
        
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if user.user_type == 'customer':
            Customer.objects.get_or_create(user = user)
        elif user.user_type == 'owner':
            pass
        elif user.user_type == 'staff':
            pass
        

        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'user_type', 'phone_number', 'password', 'password_confirm')

        read_only_fields = ('id',)
        extra_kwargs = {
            'email': {'required':True},
            'first_name': {'required':True},
            'last_name': {'required':True},
        }


class CustomerSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(user_type='customer'))
    email = serializers.EmailField(source='user.email', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = Customer
        fields = [
            'customer_id', 'user', 'email', 'phone_number', 'first_name', 'last_name',
            'date_of_birth', 'loyalty_points', 'dietary_preferences', 'newsletter_subscribed',
            'marketing_emails', 'created_at'
        ]
        read_only_fields = ['customer_id', 'created_at']

    def validate_user(self, value):
        if value.user_type != 'customer':
            raise ValidationError("User must be a customer")
        return value


class RestaurantStaffSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(user_type='staff'))
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)

    class Meta:
        model = RestaurantStaff
        fields = [
            'staff_id', 'user', 'restaurant', 'restaurant_name', 'email', 'username',
            'first_name', 'last_name', 'role', 'salary', 'hire_date', 'is_active',
            'can_manage_orders', 'can_manage_menu', 'can_manage_staff', 'can_view_reports',
            'shifts', 'created_at'
        ]
        read_only_fields = ['staff_id', 'hire_date', 'created_at']

    def validate_user(self, value):
        if value.user_type != 'staff':
            raise ValidationError("User must be staff")
        return value


class StaffCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)

    class Meta:
        model = RestaurantStaff
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'restaurant', 'role', 'salary', 'can_manage_orders', 'can_manage_menu',
            'can_manage_staff', 'can_view_reports'
        ]

    def create(self, validated_data):
        # Extract user data
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'user_type': 'staff'
        }

        # Create user
        user = User.objects.create_user(**user_data)
        
        # Create staff profile
        staff = RestaurantStaff.objects.create(user=user, **validated_data)
        return staff


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'user_type', 'phone_number', 'created_at', 'email_verified', 'is_verified')
        read_only_fields = ('id', 'created_at', 'email_verified', 'is_verified')
