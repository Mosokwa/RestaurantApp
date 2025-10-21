from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta, datetime
from ..models import Table, Reservation, TimeSlot, Restaurant, Branch
from ..services.reservation_services import ReservationService

class RestaurantReservationConfigSerializer(serializers.ModelSerializer):
    """Serializer for restaurant reservation configuration"""
    class Meta:
        model = Restaurant
        fields = [
            'reservation_enabled', 'reservation_lead_time_hours', 
            'reservation_max_days_ahead', 'max_party_size', 'min_party_size',
            'reservation_duration_options', 'requires_confirmation',
            'cancellation_policy_hours', 'deposit_required', 'deposit_amount',
            'time_slot_interval', 'allow_same_day_reservations',
            'require_phone_verification', 'auto_assign_tables', 'reservation_notes'
        ]

class TableSerializer(serializers.ModelSerializer):
    is_available_for_reservation = serializers.SerializerMethodField()
    
    class Meta:
        model = Table
        fields = [
            'table_id', 'table_number', 'table_name', 'capacity', 
            'table_type', 'is_available', 'position_x', 'position_y',
            'description', 'min_party_size', 'max_party_size', 
            'is_available_for_reservation', 'branch'
        ]
    
    def get_is_available_for_reservation(self, obj):
        request = self.context.get('request')
        if request:
            date = request.query_params.get('date')
            time = request.query_params.get('time')
            duration = request.query_params.get('duration', 90)
            
            if date and time:
                try:
                    reservation_date = datetime.strptime(date, '%Y-%m-%d').date()
                    reservation_time = datetime.strptime(time, '%H:%M').time()
                    return ReservationService.is_table_available(
                        obj, reservation_date, reservation_time, int(duration)
                    )
                except (ValueError, TypeError):
                    pass
        return None

class TimeSlotSerializer(serializers.ModelSerializer):
    available_capacity = serializers.ReadOnlyField()
    is_fully_booked = serializers.ReadOnlyField()
    
    class Meta:
        model = TimeSlot
        fields = [
            'slot_id', 'date', 'start_time', 'end_time', 
            'max_capacity', 'reserved_count', 'available_capacity',
            'is_available', 'is_fully_booked', 'restaurant', 'branch'
        ]

class ReservationSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    branch_address = serializers.CharField(source='branch.address.street_address', read_only=True)
    table_number = serializers.CharField(source='table.table_number', read_only=True)
    end_time = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    can_be_cancelled = serializers.SerializerMethodField()
    cancellation_deadline = serializers.SerializerMethodField()
    
    class Meta:
        model = Reservation
        fields = [
            'reservation_id', 'reservation_code', 'customer_name', 'customer_email',
            'restaurant_name', 'branch_address', 'table_number', 'reservation_date',
            'reservation_time', 'end_time', 'duration_minutes', 'party_size',
            'special_occasion', 'special_requests', 'status', 'is_upcoming',
            'can_be_cancelled', 'cancellation_deadline', 'created_at'
        ]
    
    def get_end_time(self, obj):
        return obj.end_time
    
    def get_is_upcoming(self, obj):
        return obj.is_upcoming
    
    def get_can_be_cancelled(self, obj):
        return obj.can_be_cancelled()
    
    def get_cancellation_deadline(self, obj):
        reservation_datetime = timezone.make_aware(
            datetime.combine(obj.reservation_date, obj.reservation_time)
        )
        cancellation_deadline = reservation_datetime - timedelta(
            hours=obj.restaurant.cancellation_policy_hours
        )
        return cancellation_deadline

class ReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            'restaurant', 'branch', 'reservation_date', 'reservation_time',
            'duration_minutes', 'party_size', 'special_occasion', 'special_requests'
        ]
    
    def validate(self, data):
        restaurant = data['restaurant']
        branch = data['branch']
        reservation_date = data['reservation_date']
        reservation_time = data['reservation_time']
        duration_minutes = data.get('duration_minutes', 90)
        party_size = data['party_size']
        
        # Use service layer for validation
        try:
            ReservationService.validate_reservation_request(
                restaurant, branch, reservation_date, reservation_time, 
                duration_minutes, party_size
            )
        except Exception as e:
            raise serializers.ValidationError(str(e))
        
        # Check availability
        available_tables = ReservationService.find_available_tables(
            restaurant, branch, reservation_date, reservation_time,
            duration_minutes, party_size
        )
        
        if not available_tables:
            raise serializers.ValidationError("No available tables for the selected time and party size")
        
        return data

class AvailabilityCheckSerializer(serializers.Serializer):
    reservation_date = serializers.DateField()
    party_size = serializers.IntegerField(min_value=1, max_value=50)
    duration_minutes = serializers.IntegerField(min_value=30, max_value=360, default=90)
    branch_id = serializers.IntegerField(required=False)
    
    def validate_reservation_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Date must be in the future")
        return value
    
    def validate_party_size(self, value):
        if value < 1:
            raise serializers.ValidationError("Party size must be at least 1")
        return value

class RestaurantsSearchSerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    time = serializers.TimeField(required=False)
    party_size = serializers.IntegerField(default=2, min_value=1, max_value=50)
    location = serializers.CharField(required=False, max_length=100)
    cuisine = serializers.CharField(required=False, max_length=50)
    max_distance = serializers.IntegerField(required=False, help_text="Maximum distance in miles")
    
    def validate_date(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError("Date must be in the future")
        return value