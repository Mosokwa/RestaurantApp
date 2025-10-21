from datetime import timedelta
from django.utils import timezone 
from rest_framework import status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from ..models import DishRating, DishReview, RestaurantRating, RestaurantReview, ReviewHelpfulVote, ReviewReport, ReviewResponse, Restaurant, MenuItem, Order
from ..serializers import (
    BulkRatingSerializer, DishRatingSerializer, DishReviewSerializer, QuickRatingSerializer, RatingStatsSerializer, RestaurantRatingSerializer, RestaurantReviewSerializer, ReviewAnalyticsSerializer, ReviewHelpfulVoteSerializer, ReviewReportSerializer, ReviewResponseSerializer
)

class RestaurantReviewListView(generics.ListCreateAPIView):
    serializer_class = RestaurantReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['overall_rating', 'status']
    ordering_fields = ['created_at', 'overall_rating', 'helpful_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        restaurant_id = self.kwargs.get('restaurant_id')
        queryset = RestaurantReview.objects.filter(
            restaurant_id=restaurant_id,
            status='approved'
        ).select_related('customer__user', 'restaurant', 'order')
        
        # Restaurant owners can see all reviews including pending ones
        if self.request.user.is_authenticated:
            try:
                restaurant = Restaurant.objects.get(pk=restaurant_id)
                if (self.request.user == restaurant.owner or 
                    restaurant.staff_members.filter(user=self.request.user).exists()):
                    queryset = RestaurantReview.objects.filter(restaurant_id=restaurant_id)
            except Restaurant.DoesNotExist:
                pass
        
        return queryset
    
    def perform_create(self, serializer):
        restaurant_id = self.kwargs.get('restaurant_id')
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        
        # Check if user has already reviewed this restaurant
        customer = self.request.user.customer_profile
        if RestaurantReview.objects.filter(restaurant=restaurant, customer=customer).exists():
            raise ValidationError("You have already reviewed this restaurant")
        
        # Check if review settings require order verification
        if (hasattr(restaurant, 'review_settings') and 
            restaurant.review_settings.require_order_verification):
            
            # Verify that customer has ordered from this restaurant
            has_ordered = Order.objects.filter(
                customer=customer,
                restaurant=restaurant,
                status='delivered'
            ).exists()
            
            if not has_ordered:
                raise PermissionDenied("You must have ordered from this restaurant to leave a review")
        
        serializer.save(restaurant=restaurant)

class DishReviewListView(generics.ListCreateAPIView):
    serializer_class = DishReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['rating', 'status']
    ordering_fields = ['created_at', 'rating', 'helpful_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        menu_item_id = self.kwargs.get('menu_item_id')
        return DishReview.objects.filter(
            menu_item_id=menu_item_id,
            status='approved'
        ).select_related('customer__user', 'menu_item', 'menu_item__category__restaurant')
    
    def perform_create(self, serializer):
        menu_item_id = self.kwargs.get('menu_item_id')
        menu_item = get_object_or_404(MenuItem, pk=menu_item_id)
        
        # Check if user has already reviewed this dish
        customer = self.request.user.customer_profile
        if DishReview.objects.filter(menu_item=menu_item, customer=customer).exists():
            raise ValidationError("You have already reviewed this menu item")
        
        serializer.save(menu_item=menu_item)

class ReviewResponseView(generics.CreateAPIView):
    serializer_class = ReviewResponseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ReviewResponse.objects.select_related('review', 'review__restaurant', 'responder')
    
    def perform_create(self, serializer):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(RestaurantReview, pk=review_id)
        
        # Check if user is restaurant owner or staff
        restaurant = review.restaurant
        if not (self.request.user == restaurant.owner or 
               restaurant.staff_members.filter(user=self.request.user).exists()):
            raise PermissionDenied("Only restaurant owners or staff can respond to reviews")
        
        # Check if response already exists
        if ReviewResponse.objects.filter(review=review).exists():
            raise ValidationError("A response already exists for this review")
        
        serializer.save(review=review)

class ReviewHelpfulVoteView(generics.CreateAPIView):
    serializer_class = ReviewHelpfulVoteSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(RestaurantReview, pk=review_id)
        customer = request.user.customer_profile
        
        # Check if user has already voted
        existing_vote = ReviewHelpfulVote.objects.filter(
            review=review, 
            customer=customer
        ).first()
        
        if existing_vote:
            # Update existing vote
            is_helpful = request.data.get('is_helpful', True)
            if existing_vote.is_helpful != is_helpful:
                existing_vote.is_helpful = is_helpful
                existing_vote.save()
        else:
            # Create new vote
            serializer = self.get_serializer(data={
                'review': review.review_id,
                'is_helpful': request.data.get('is_helpful', True)
            })
            serializer.is_valid(raise_exception=True)
            serializer.save()
        
        # Update helpful count
        review.helpful_count = review.helpful_votes.filter(is_helpful=True).count()
        review.save()
        
        return Response({
            'helpful_count': review.helpful_count,
            'user_has_voted': True,
            'user_vote_type': True  # Assuming the vote was helpful
        })

class ReviewReportView(generics.CreateAPIView):
    serializer_class = ReviewReportSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(RestaurantReview, pk=review_id)
        
        # Check if user has already reported this review
        if ReviewReport.objects.filter(review=review, reporter=self.request.user).exists():
            raise ValidationError("You have already reported this review")
        
        serializer.save(review=review)

class RestaurantReviewAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, restaurant_id):
        try:
            restaurant = Restaurant.objects.get(pk=restaurant_id)
            
            # Check if user has access to this restaurant's analytics
            if not (request.user == restaurant.owner or 
                   restaurant.staff_members.filter(user=request.user).exists()):
                return Response(
                    {'error': 'You do not have permission to view analytics for this restaurant'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Calculate analytics
            analytics = self._calculate_review_analytics(restaurant)
            serializer = ReviewAnalyticsSerializer(analytics)
            
            return Response(serializer.data)
            
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Restaurant not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _calculate_review_analytics(self, restaurant):
        # Get all approved reviews
        reviews = restaurant.reviews.filter(status='approved')
        
        # Basic metrics
        total_reviews = reviews.count()
        average_rating = reviews.aggregate(avg_rating=Avg('overall_rating'))['avg_rating'] or 0
        
        # Rating breakdown
        rating_breakdown = reviews.values('overall_rating').annotate(
            count=Count('review_id')
        ).order_by('overall_rating')
        
        # Recent reviews (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_reviews_count = reviews.filter(created_at__gte=thirty_days_ago).count()
        
        # Response rate
        reviews_with_responses = reviews.filter(response__isnull=False).count()
        response_rate = (reviews_with_responses / total_reviews * 100) if total_reviews > 0 else 0
        
        # Reported reviews
        reported_reviews_count = ReviewReport.objects.filter(
            review__restaurant=restaurant,
            status='pending'
        ).count()
        
        return {
            'total_reviews': total_reviews,
            'average_rating': float(average_rating),
            'rating_breakdown': list(rating_breakdown),
            'recent_reviews_count': recent_reviews_count,
            'response_rate': round(float(response_rate), 2),
            'reported_reviews_count': reported_reviews_count
        }

class UserReviewsView(generics.ListAPIView):
    serializer_class = RestaurantReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return RestaurantReview.objects.filter(
            customer=self.request.user.customer_profile
        ).select_related('restaurant', 'order').order_by('-created_at')

class ReviewModerationListView(generics.ListAPIView):
    serializer_class = RestaurantReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        restaurant_id = self.kwargs.get('restaurant_id')
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        
        # Check if user has moderation permissions
        if not (self.request.user == restaurant.owner or 
               restaurant.staff_members.filter(user=self.request.user, can_manage_orders=True).exists()):
            raise PermissionDenied("You do not have permission to moderate reviews")
        
        return RestaurantReview.objects.filter(
            restaurant=restaurant,
            status__in=['pending', 'reported']
        ).select_related('customer__user', 'order')

class ReviewModerationUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, review_id):
        review = get_object_or_404(RestaurantReview, pk=review_id)
        restaurant = review.restaurant
        
        # Check if user has moderation permissions
        if not (request.user == restaurant.owner or 
               restaurant.staff_members.filter(user=request.user, can_manage_orders=True).exists()):
            raise PermissionDenied("You do not have permission to moderate reviews")
        
        action = request.data.get('action')
        notes = request.data.get('notes', '')
        
        if action == 'approve':
            review.status = 'approved'
            review.approved_at = timezone.now()
            review.save()
            
            # Update restaurant rating
            restaurant.update_rating(float(review.overall_rating))
            
        elif action == 'reject':
            review.status = 'rejected'
            review.save()
            
        elif action == 'resolve_report':
            if review.status == 'reported':
                review.status = 'approved'  # or keep as approved if it was approved before reporting
                review.save()
                
                # Resolve all reports for this review
                ReviewReport.objects.filter(review=review, status='pending').update(
                    status='resolved',
                    resolved_by=request.user,
                    resolved_at=timezone.now(),
                    moderator_notes=notes
                )
        
        return Response({'status': 'success', 'review_status': review.status})

class RestaurantRatingView(APIView):
    """
    Handle restaurant ratings - GET to check user's rating, POST to create/update rating
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, restaurant_id):
        """Get the current user's rating for this restaurant"""
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        
        user_rating = restaurant.get_user_rating(request.user)
        
        if user_rating:
            serializer = RestaurantRatingSerializer(user_rating)
            return Response(serializer.data)
        else:
            return Response({'has_rated': False})
    
    def post(self, request, restaurant_id):
        """Create or update a rating for the restaurant"""
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        customer = request.user.customer_profile
        
        # Check if user has already rated this restaurant
        existing_rating = RestaurantRating.objects.filter(
            restaurant=restaurant,
            customer=customer
        ).first()
        
        if existing_rating:
            # Update existing rating
            serializer = RestaurantRatingSerializer(
                existing_rating, 
                data=request.data, 
                partial=True
            )
        else:
            # Create new rating
            serializer = RestaurantRatingSerializer(data=request.data)
        
        if serializer.is_valid():
            # Ensure the rating belongs to the correct restaurant and customer
            rating_data = serializer.validated_data.copy()
            rating_data['restaurant'] = restaurant
            rating_data['customer'] = customer
            
            # Link to order if provided
            order_id = request.data.get('order_id')
            if order_id:
                try:
                    order = Order.objects.get(
                        order_id=order_id,
                        customer=customer,
                        restaurant=restaurant
                    )
                    rating_data['order'] = order
                except Order.DoesNotExist:
                    pass
            
            if existing_rating:
                rating = serializer.save(**rating_data)
            else:
                rating = serializer.create(rating_data)
            
            return Response(RestaurantRatingSerializer(rating).data, 
                          status=status.HTTP_200_OK if existing_rating else status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, restaurant_id):
        """Delete the user's rating for this restaurant"""
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        customer = request.user.customer_profile
        
        try:
            rating = RestaurantRating.objects.get(
                restaurant=restaurant,
                customer=customer
            )
            rating.delete()
            
            # Update restaurant rating stats
            restaurant.update_rating_stats()
            
            return Response({'message': 'Rating deleted successfully'})
        except RestaurantRating.DoesNotExist:
            return Response(
                {'error': 'No rating found to delete'},
                status=status.HTTP_404_NOT_FOUND
            )

class DishRatingView(APIView):
    """
    Handle dish ratings - GET to check user's rating, POST to create/update rating
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, menu_item_id):
        """Get the current user's rating for this menu item"""
        menu_item = get_object_or_404(MenuItem, pk=menu_item_id)
        
        user_rating = menu_item.get_user_rating(request.user)
        
        if user_rating:
            serializer = DishRatingSerializer(user_rating)
            return Response(serializer.data)
        else:
            return Response({'has_rated': False})
    
    def post(self, request, menu_item_id):
        """Create or update a rating for the menu item"""
        menu_item = get_object_or_404(MenuItem, pk=menu_item_id)
        customer = request.user.customer_profile
        
        # Check if user has already rated this dish
        existing_rating = DishRating.objects.filter(
            menu_item=menu_item,
            customer=customer
        ).first()
        
        if existing_rating:
            serializer = DishRatingSerializer(
                existing_rating, 
                data=request.data, 
                partial=True
            )
        else:
            serializer = DishRatingSerializer(data=request.data)
        
        if serializer.is_valid():
            rating_data = serializer.validated_data.copy()
            rating_data['menu_item'] = menu_item
            rating_data['customer'] = customer
            
            # Link to order if provided
            order_id = request.data.get('order_id')
            if order_id:
                try:
                    order = Order.objects.get(
                        order_id=order_id,
                        customer=customer
                    )
                    rating_data['order'] = order
                except Order.DoesNotExist:
                    pass
            
            if existing_rating:
                rating = serializer.save(**rating_data)
            else:
                rating = serializer.create(rating_data)
            
            return Response(DishRatingSerializer(rating).data, 
                          status=status.HTTP_200_OK if existing_rating else status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, menu_item_id):
        """Delete the user's rating for this menu item"""
        menu_item = get_object_or_404(MenuItem, pk=menu_item_id)
        customer = request.user.customer_profile
        
        try:
            rating = DishRating.objects.get(
                menu_item=menu_item,
                customer=customer
            )
            rating.delete()
            
            # Update menu item rating stats
            menu_item.update_rating_stats()
            
            return Response({'message': 'Rating deleted successfully'})
        except DishRating.DoesNotExist:
            return Response(
                {'error': 'No rating found to delete'},
                status=status.HTTP_404_NOT_FOUND
            )

class QuickRatingView(APIView):
    """
    Handle quick ratings (just overall rating without detailed breakdown)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, restaurant_id):
        """Create a quick rating for a restaurant"""
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        customer = request.user.customer_profile
        
        serializer = QuickRatingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Check for existing rating
        existing_rating = RestaurantRating.objects.filter(
            restaurant=restaurant,
            customer=customer
        ).first()
        
        if existing_rating:
            # Update existing rating with quick rating data
            existing_rating.overall_rating = serializer.validated_data['overall_rating']
            existing_rating.tags = serializer.validated_data.get('tags', [])
            existing_rating.is_quick_rating = True
            existing_rating.save()
            
            rating = existing_rating
        else:
            # Create new quick rating
            rating = RestaurantRating.objects.create(
                restaurant=restaurant,
                customer=customer,
                overall_rating=serializer.validated_data['overall_rating'],
                tags=serializer.validated_data.get('tags', []),
                is_quick_rating=True
            )
        
        return Response(RestaurantRatingSerializer(rating).data, status=status.HTTP_201_CREATED)

class RatingStatsView(APIView):
    """
    Get comprehensive rating statistics for a restaurant or menu item
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        object_type = request.query_params.get('type')  # 'restaurant' or 'menu_item'
        object_id = request.query_params.get('id')
        
        if not object_type or not object_id:
            return Response(
                {'error': 'Type and ID parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if object_type == 'restaurant':
            try:
                restaurant = Restaurant.objects.get(pk=object_id)
                stats = restaurant.get_rating_stats()
                
                # Add user's rating if authenticated
                user_rating = None
                if request.user.is_authenticated:
                    user_rating_obj = restaurant.get_user_rating(request.user)
                    user_rating = user_rating_obj.overall_rating if user_rating_obj else None
                
                stats['user_rating'] = user_rating
                serializer = RatingStatsSerializer(stats)
                return Response(serializer.data)
                
            except Restaurant.DoesNotExist:
                return Response(
                    {'error': 'Restaurant not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif object_type == 'menu_item':
            try:
                menu_item = MenuItem.objects.get(pk=object_id)
                stats = menu_item.get_rating_stats()
                
                # Add user's rating if authenticated
                user_rating = None
                if request.user.is_authenticated:
                    user_rating_obj = menu_item.get_user_rating(request.user)
                    user_rating = user_rating_obj.rating if user_rating_obj else None
                
                stats['user_rating'] = user_rating
                serializer = RatingStatsSerializer(stats)
                return Response(serializer.data)
                
            except MenuItem.DoesNotExist:
                return Response(
                    {'error': 'Menu item not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        else:
            return Response(
                {'error': 'Invalid type. Use "restaurant" or "menu_item"'},
                status=status.HTTP_400_BAD_REQUEST
            )

class BulkRatingView(APIView):
    """
    Handle bulk rating operations (rating multiple restaurants/dishes at once)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = BulkRatingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        customer = request.user.customer_profile
        results = {
            'restaurant_ratings': [],
            'dish_ratings': []
        }
        
        # Process restaurant ratings
        for rating_data in serializer.validated_data.get('restaurant_ratings', []):
            try:
                restaurant = Restaurant.objects.get(pk=rating_data['restaurant_id'])
                
                # Check for existing rating
                existing_rating = RestaurantRating.objects.filter(
                    restaurant=restaurant,
                    customer=customer
                ).first()
                
                if existing_rating:
                    # Update
                    for field in ['overall_rating', 'food_quality', 'service_quality', 'ambiance', 'value_for_money', 'tags']:
                        if field in rating_data:
                            setattr(existing_rating, field, rating_data[field])
                    existing_rating.save()
                    rating = existing_rating
                else:
                    # Create
                    rating = RestaurantRating.objects.create(
                        restaurant=restaurant,
                        customer=customer,
                        **{k: v for k, v in rating_data.items() if k != 'restaurant_id'}
                    )
                
                results['restaurant_ratings'].append({
                    'restaurant_id': restaurant.restaurant_id,
                    'rating_id': rating.rating_id,
                    'status': 'updated' if existing_rating else 'created'
                })
                
            except Restaurant.DoesNotExist:
                results['restaurant_ratings'].append({
                    'restaurant_id': rating_data['restaurant_id'],
                    'error': 'Restaurant not found'
                })
        
        # Process dish ratings
        for rating_data in serializer.validated_data.get('dish_ratings', []):
            try:
                menu_item = MenuItem.objects.get(pk=rating_data['menu_item_id'])
                
                # Check for existing rating
                existing_rating = DishRating.objects.filter(
                    menu_item=menu_item,
                    customer=customer
                ).first()
                
                if existing_rating:
                    # Update
                    for field in ['rating', 'taste', 'portion_size', 'value', 'tags']:
                        if field in rating_data:
                            setattr(existing_rating, field, rating_data[field])
                    existing_rating.save()
                    rating = existing_rating
                else:
                    # Create
                    rating = DishRating.objects.create(
                        menu_item=menu_item,
                        customer=customer,
                        **{k: v for k, v in rating_data.items() if k != 'menu_item_id'}
                    )
                
                results['dish_ratings'].append({
                    'menu_item_id': menu_item.item_id,
                    'rating_id': rating.dish_rating_id,
                    'status': 'updated' if existing_rating else 'created'
                })
                
            except MenuItem.DoesNotExist:
                results['dish_ratings'].append({
                    'menu_item_id': rating_data['menu_item_id'],
                    'error': 'Menu item not found'
                })
        
        return Response(results, status=status.HTTP_200_OK)

class UserRatingsView(generics.ListAPIView):
    """
    Get all ratings by the current user
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        # This would need to be a serializer that can handle both restaurant and dish ratings
        pass
    
    def get_queryset(self):
        customer = self.request.user.customer_profile
        
        # Get both restaurant and dish ratings
        restaurant_ratings = RestaurantRating.objects.filter(customer=customer)
        dish_ratings = DishRating.objects.filter(customer=customer)
        
        # Combine and sort by creation date
        # This is a simplified approach - you might want to handle this differently
        return list(restaurant_ratings) + list(dish_ratings)
    
    def list(self, request, *args, **kwargs):
        customer = request.user.customer_profile
        
        restaurant_ratings = RestaurantRating.objects.filter(
            customer=customer
        ).select_related('restaurant', 'order')
        
        dish_ratings = DishRating.objects.filter(
            customer=customer
        ).select_related('menu_item', 'menu_item__category__restaurant', 'order')
        
        restaurant_serializer = RestaurantRatingSerializer(restaurant_ratings, many=True)
        dish_serializer = DishRatingSerializer(dish_ratings, many=True)
        
        return Response({
            'restaurant_ratings': restaurant_serializer.data,
            'dish_ratings': dish_serializer.data,
            'total_ratings': restaurant_ratings.count() + dish_ratings.count()
        })
