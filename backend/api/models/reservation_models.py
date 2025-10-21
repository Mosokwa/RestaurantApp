# reservation_models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from datetime import timedelta

class Table(models.Model):
    TABLE_TYPES = (
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
        ('booth', 'Booth'),
        ('bar', 'Bar'),
        ('private', 'Private Room'),
    )
    
    table_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant', 
        on_delete=models.CASCADE, 
        related_name='tables'
    )
    branch = models.ForeignKey(
        'api.Branch', 
        on_delete=models.CASCADE, 
        related_name='tables'
    )
    table_number = models.CharField(max_length=10)
    table_name = models.CharField(max_length=50, blank=True, null=True)
    capacity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(50)])
    table_type = models.CharField(max_length=20, choices=TABLE_TYPES, default='indoor')
    is_available = models.BooleanField(default=True)
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    min_party_size = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    max_party_size = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(50)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tables'
        ordering = ['branch', 'table_number']
        unique_together = ['branch', 'table_number']
        indexes = [
            models.Index(fields=['branch', 'is_available']),
            models.Index(fields=['table_type', 'capacity']),
        ]

    def __str__(self):
        name_part = f" - {self.table_name}" if self.table_name else ""
        return f"{self.table_number}{name_part} ({self.capacity} people)"

    def is_available_for_reservation(self, date, time, duration_minutes=90):
        """Check if table is available for a specific time slot"""
        from .reservation_models import Reservation
        
        reservation_time = timezone.datetime.combine(date, time)
        reservation_end = reservation_time + timedelta(minutes=duration_minutes)
        
        # Check for overlapping reservations
        overlapping_reservations = Reservation.objects.filter(
            table=self,
            reservation_date=date,
            status__in=['confirmed', 'pending', 'seated'],
        ).exclude(
            models.Q(reservation_time__gte=reservation_end.time()) |
            models.Q(
                models.F('reservation_time') + 
                models.F('duration_minutes') * timedelta(minutes=1) <= reservation_time.time()
            )
        )
        
        return not overlapping_reservations.exists()

    def get_availability_schedule(self, date):
        """Get availability schedule for a specific date"""
        from .reservation_models import Reservation
        
        reservations = Reservation.objects.filter(
            table=self,
            reservation_date=date,
            status__in=['confirmed', 'pending', 'seated']
        ).order_by('reservation_time')
        
        return reservations
    
    def generate_qr_code(self, base_url):
        """Generate QR code for this specific table"""
        import qrcode
        from io import BytesIO
        import base64
        
        qr_data = f"{base_url}?table={self.table_number}&branch={self.branch.branch_id}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{qr_code_base64}"


class TimeSlot(models.Model):
    slot_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant', 
        on_delete=models.CASCADE, 
        related_name='time_slots'
    )
    branch = models.ForeignKey(
        'api.Branch', 
        on_delete=models.CASCADE, 
        related_name='time_slots'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_capacity = models.IntegerField(validators=[MinValueValidator(1)])
    reserved_count = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'time_slots'
        ordering = ['date', 'start_time']
        unique_together = ['branch', 'date', 'start_time']
        indexes = [
            models.Index(fields=['branch', 'date', 'is_available']),
            models.Index(fields=['date', 'start_time']),
        ]

    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time} ({self.branch})"

    @property
    def available_capacity(self):
        return self.max_capacity - self.reserved_count

    def is_fully_booked(self):
        return self.reserved_count >= self.max_capacity

    def update_reserved_count(self):
        """Update reserved count based on actual reservations"""
        from .reservation_models import Reservation
        
        reserved_count = Reservation.objects.filter(
            branch=self.branch,
            reservation_date=self.date,
            reservation_time=self.start_time,
            status__in=['confirmed', 'pending', 'seated']
        ).count()
        
        self.reserved_count = reserved_count
        self.save()


class Reservation(models.Model):
    OCCASION_CHOICES = (
        ('none', 'None'),
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('business', 'Business Meeting'),
        ('date', 'Romantic Date'),
        ('family', 'Family Gathering'),
        ('celebration', 'Celebration'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('seated', 'Seated'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )
    
    reservation_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        'api.Customer', 
        on_delete=models.CASCADE, 
        related_name='reservations'
    )
    restaurant = models.ForeignKey(
        'api.Restaurant', 
        on_delete=models.CASCADE, 
        related_name='reservations'
    )
    branch = models.ForeignKey(
        'api.Branch', 
        on_delete=models.CASCADE, 
        related_name='reservations'
    )
    table = models.ForeignKey(
        Table, 
        on_delete=models.CASCADE, 
        related_name='reservations', 
        null=True, 
        blank=True
    )
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    duration_minutes = models.IntegerField(
        default=90,
        validators=[MinValueValidator(30), MaxValueValidator(360)]
    )
    party_size = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(50)])
    special_occasion = models.CharField(
        max_length=20, 
        choices=OCCASION_CHOICES, 
        default='none'
    )
    special_requests = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reservation_code = models.CharField(max_length=8, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notification fields
    confirmation_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'reservations'
        ordering = ['-reservation_date', '-reservation_time']
        indexes = [
            models.Index(fields=['reservation_date', 'reservation_time']),
            models.Index(fields=['status', 'reservation_date']),
            models.Index(fields=['reservation_code']),
            models.Index(fields=['customer', 'created_at']),
        ]

    def __str__(self):
        return f"Reservation #{self.reservation_code} - {self.customer} - {self.reservation_date} {self.reservation_time}"

    def save(self, *args, **kwargs):
        if not self.reservation_code:
            self.reservation_code = self.generate_reservation_code()
        super().save(*args, **kwargs)

    def generate_reservation_code(self):
        """Generate unique reservation code"""
        import random
        import string
        
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Reservation.objects.filter(reservation_code=code).exists():
                return code

    @property
    def end_time(self):
        reservation_datetime = timezone.datetime.combine(
            self.reservation_date, 
            self.reservation_time
        )
        end_datetime = reservation_datetime + timedelta(minutes=self.duration_minutes)
        return end_datetime.time()

    @property
    def is_upcoming(self):
        """Check if reservation is in the future"""
        now = timezone.now()
        reservation_datetime = timezone.datetime.combine(
            self.reservation_date, 
            self.reservation_time
        )
        return reservation_datetime > now

    @property
    def is_active(self):
        """Check if reservation is active (not completed or cancelled)"""
        return self.status in ['pending', 'confirmed', 'seated']

    def check_time_conflicts(self):
        """Check for time conflicts with other reservations"""
        conflicts = Reservation.objects.filter(
            table=self.table,
            reservation_date=self.reservation_date,
            status__in=['confirmed', 'pending', 'seated'],
        ).exclude(pk=self.pk).filter(
            models.Q(reservation_time__lt=self.end_time) &
            models.Q(
                models.F('reservation_time') + 
                models.F('duration_minutes') * timedelta(minutes=1) > self.reservation_time
            )
        )
        return conflicts.exists()

    def can_be_cancelled(self):
        """Check if reservation can be cancelled based on cancellation policy"""
        if self.status in ['cancelled', 'completed', 'no_show']:
            return False
            
        reservation_datetime = timezone.datetime.combine(
            self.reservation_date, 
            self.reservation_time
        )
        now = timezone.now()
        
        # Allow cancellation up to 1 hour before reservation
        return (reservation_datetime - now) > timedelta(hours=1)

    def cancel(self, reason=""):
        """Cancel reservation with reason"""
        if self.can_be_cancelled():
            self.status = 'cancelled'
            self.cancellation_reason = reason
            self.save()
            return True
        return False

    def confirm(self):
        """Confirm reservation"""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.save()
            return True
        return False

    def mark_seated(self):
        """Mark reservation as seated"""
        if self.status == 'confirmed':
            self.status = 'seated'
            self.save()
            return True
        return False

    def mark_completed(self):
        """Mark reservation as completed"""
        if self.status in ['confirmed', 'seated']:
            self.status = 'completed'
            self.save()
            return True
        return False