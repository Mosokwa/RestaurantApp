from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction
from ..models import User, Restaurant, RestaurantStaff, RestaurantOwnership

class OwnerLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class OwnerRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    restaurant_name = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'restaurant_name'
        )
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise ValidationError("Passwords don't match")
        
        if User.objects.filter(email=data['email']).exists():
            raise ValidationError("A user with this email already exists.")
        
        return data
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise ValidationError("A user with this email already exists.")
        return value.lower()
    
    @transaction.atomic
    def create(self, validated_data):
        # Remove confirmation field and restaurant name
        validated_data.pop('password_confirm')
        restaurant_name = validated_data.pop('restaurant_name', None)
        password = validated_data.pop('password')
        
        # Create user with owner type
        validated_data['user_type'] = 'owner'
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create initial restaurant if name provided
        if restaurant_name:
            restaurant = Restaurant.objects.create(
                owner=user,
                name=restaurant_name,
                status='pending'
            )
            # Set ownership relationship
            RestaurantOwnership.objects.create(
                user=user,
                restaurant=restaurant,
                is_primary_owner=True
            )
        
        return user

class OwnerProfileSerializer(serializers.ModelSerializer):
    restaurants = serializers.SerializerMethodField()
    total_restaurants = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'phone_number', 'user_type', 'is_restaurant_owner',
            'restaurants', 'total_restaurants', 'date_joined',
            'email_verified', 'is_verified'
        )
        read_only_fields = ('id', 'user_type', 'is_restaurant_owner', 'date_joined', 'email_verified', 'is_verified')
    
    def get_restaurants(self, obj):
        from .restaurantSerializers import RestaurantSerializer
        restaurants = Restaurant.objects.filter(owner=obj)
        return RestaurantSerializer(restaurants, many=True).data
    
    def get_total_restaurants(self, obj):
        return Restaurant.objects.filter(owner=obj).count()

class StaffInviteSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=RestaurantStaff.ROLE_CHOICES)
    branch_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = RestaurantStaff
        fields = (
            'email', 'first_name', 'last_name', 'restaurant', 
            'role', 'salary', 'branch_ids'
        )
    
    def validate(self, data):
        request = self.context.get('request')
        restaurant = data.get('restaurant')
        
        # Verify that the requesting user owns this restaurant
        if restaurant.owner != request.user:
            raise ValidationError("You can only invite staff to your own restaurants.")
        
        # Check if user already exists and is not already staff
        email = data.get('email')
        try:
            user = User.objects.get(email=email)
            if hasattr(user, 'staff_profile') and user.staff_profile.restaurant == restaurant:
                raise ValidationError("This user is already staff at this restaurant.")
        except User.DoesNotExist:
            pass
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        restaurant = validated_data['restaurant']
        email = validated_data['email']
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        role = validated_data['role']
        salary = validated_data.get('salary')
        branch_ids = validated_data.pop('branch_ids', [])
        
        # Get or create user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user account
            username = email.split('@')[0]
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                user_type='staff',
                is_active=True
            )
        
        # Create staff profile
        staff = RestaurantStaff.objects.create(
            user=user,
            restaurant=restaurant,
            role=role,
            salary=salary
        )
        
        # Set branch access if specified
        if branch_ids:
            from ..models import Branch
            branches = Branch.objects.filter(
                branch_id__in=branch_ids, 
                restaurant=restaurant
            )
            staff.branch_access.set(branches)
        
        # TODO: Send invitation email
        
        return staff