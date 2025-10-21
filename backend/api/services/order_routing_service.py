# services/order_routing_service.py
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import logging


logger = logging.getLogger(__name__)

class OrderRoutingService:
    """Service for intelligent order routing to kitchen stations"""
    
    def __init__(self, order):
        self.order = order
        self.restaurant = order.restaurant
        self.branch = order.branch
    
    def route_order(self):
        """Route order items to appropriate kitchen stations"""
        from ..models import OrderItemPreparation, KitchenStation
        
        routing_result = {
            'order_id': self.order.order_uuid,
            'routed_items': [],
            'failed_items': [],
            'estimated_completion': None
        }
        
        max_estimated_time = timezone.now()
        
        try:
            with transaction.atomic():
                for order_item in self.order.order_items.all():
                    station = self.find_best_station(order_item)
                    
                    if station:
                        # Create or update preparation info
                        prep_info, created = OrderItemPreparation.objects.get_or_create(
                            order_item=order_item
                        )
                        prep_info.assign_to_station(station)
                        
                        # Calculate estimated completion
                        item_estimated_time = prep_info.estimated_completion_at
                        if item_estimated_time and item_estimated_time > max_estimated_time:
                            max_estimated_time = item_estimated_time
                        
                        routing_result['routed_items'].append({
                            'item_id': order_item.order_item_id,
                            'item_name': order_item.menu_item.name,
                            'station_id': station.station_id,
                            'station_name': station.name,
                            'estimated_completion': item_estimated_time.isoformat() if item_estimated_time else None
                        })
                    else:
                        routing_result['failed_items'].append({
                            'item_id': order_item.order_item_id,
                            'item_name': order_item.menu_item.name,
                            'reason': 'No suitable station found'
                        })
                
                # Update order's estimated ready time
                if max_estimated_time > timezone.now():
                    if hasattr(self.order, 'pos_info'):
                        self.order.pos_info.estimated_ready_at = max_estimated_time
                        self.order.pos_info.save()
                    
                    routing_result['estimated_completion'] = max_estimated_time.isoformat()
            
            return routing_result
            
        except Exception as e:
            logger.error(f"Order routing failed for order {self.order.order_uuid}: {str(e)}")
            routing_result['error'] = str(e)
            return routing_result
    
    def find_best_station(self, order_item):
        """Find the best kitchen station for an order item using weighted scoring"""
        from ..models import KitchenStation
        
        menu_item = order_item.menu_item
        available_stations = KitchenStation.objects.filter(
            restaurant=self.restaurant,
            branch=self.branch,
            is_available=True
        ).prefetch_related('assigned_categories', 'assigned_staff')
        
        best_station = None
        best_score = -1
        
        for station in available_stations:
            score = self.calculate_station_score(station, menu_item)
            
            if score > best_score and score > 0:  # Only consider stations with positive score
                best_score = score
                best_station = station
        
        return best_station
    
    def calculate_station_score(self, station, menu_item):
        """Calculate weighted suitability score for station-item pairing"""
        score = 0
        
        # 1. Category matching (40% weight)
        category_score = self._calculate_category_score(station, menu_item)
        score += category_score * 0.4
        
        # 2. Workload assessment (30% weight)
        workload_score = self._calculate_workload_score(station)
        score += workload_score * 0.3
        
        # 3. Staff availability (20% weight)
        staff_score = self._calculate_staff_score(station)
        score += staff_score * 0.2
        
        # 4. Historical performance (10% weight)
        performance_score = self._calculate_performance_score(station, menu_item)
        score += performance_score * 0.1
        
        return score
    
    def _calculate_category_score(self, station, menu_item):
        """Calculate score based on category matching"""
        item_categories = set(menu_item.categories.values_list('id', flat=True))
        station_categories = set(station.assigned_categories.values_list('id', flat=True))
        
        if item_categories.intersection(station_categories):
            return 100  # Exact category match
        elif menu_item.categories.filter(parent__in=station.assigned_categories.all()).exists():
            return 80   # Parent category match
        else:
            # Check for similar items previously prepared at this station
            similar_items_count = self.order.restaurant.menu_items.filter(
                categories__in=station.assigned_categories.all(),
                preparation_time__range=(menu_item.preparation_time-5, menu_item.preparation_time+5)
            ).count()
            
            if similar_items_count > 0:
                return 60  # Similar items handled
            else:
                return 0   # No match
    
    def _calculate_workload_score(self, station):
        """Calculate score based on current workload"""
        workload = station.get_current_workload()
        workload_percentage = workload['workload_percentage']
        
        if workload_percentage <= 40:
            return 100  # Available
        elif workload_percentage <= 70:
            return 75   # Moderate
        elif workload_percentage <= 90:
            return 50   # Busy
        else:
            return 0    # Overloaded
    
    def _calculate_staff_score(self, station):
        """Calculate score based on staff availability"""
        available_staff = station.assigned_staff.filter(is_available=True).count()
        total_staff = station.assigned_staff.count()
        
        if total_staff == 0:
            return 0
        
        availability_ratio = available_staff / total_staff
        
        if availability_ratio >= 0.8:
            return 100
        elif availability_ratio >= 0.5:
            return 75
        elif availability_ratio >= 0.3:
            return 50
        else:
            return 25
    
    def _calculate_performance_score(self, station, menu_item):
        """Calculate score based on historical performance"""
        from ..models import OrderItemPreparation
        
        # Get completion rate for similar items
        similar_items = OrderItemPreparation.objects.filter(
            assigned_station=station,
            order_item__menu_item__categories__in=menu_item.categories.all(),
            preparation_status='ready'
        ).count()
        
        total_similar = OrderItemPreparation.objects.filter(
            assigned_station=station,
            order_item__menu_item__categories__in=menu_item.categories.all()
        ).count()
        
        if total_similar == 0:
            return 50  # Neutral score for no historical data
        
        completion_rate = similar_items / total_similar
        
        if completion_rate >= 0.9:
            return 100
        elif completion_rate >= 0.7:
            return 75
        elif completion_rate >= 0.5:
            return 50
        else:
            return 25
    
    def get_route_suggestions(self):
        """Get multiple routing suggestions for optimization"""
        from ..models import KitchenStation
        
        stations = KitchenStation.objects.filter(
            restaurant=self.restaurant,
            branch=self.branch,
            is_available=True
        )
        
        suggestions = []
        
        for station in stations:
            score = self.calculate_station_score(station, self.order.order_items.first().menu_item)
            if score > 0:
                suggestions.append({
                    'station': station,
                    'score': score,
                    'workload': station.get_current_workload(),
                    'estimated_time': self._estimate_preparation_time(station)
                })
        
        return sorted(suggestions, key=lambda x: x['score'], reverse=True)
    
    def _estimate_preparation_time(self, station):
        """Estimate preparation time for this station"""
        base_time = station.avg_prep_time
        workload = station.get_current_workload()
        
        # Adjust time based on workload
        workload_factor = 1 + (workload['workload_percentage'] / 100)
        estimated_time = base_time * workload_factor
        
        return timezone.now() + timedelta(minutes=estimated_time)