from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (
    RetrieveModelMixin, ListModelMixin
)
from django.db import models
from django.utils import timezone
import logging

from ..models import (
    CustomerLoyalty, Reward, Restaurant, PointsTransaction, RewardRedemption
)
from ..serializers import (
    CustomerLoyaltySerializer, RewardSerializer,
    RewardRedemptionSerializer, RestaurantLoyaltySettingsSerializer, PointsRedemptionSerializer, ReferralSerializer, MultiRestaurantLoyaltyProgramSerializer, PointsTransactionSerializer
)
from ..services.loyalty_services import MultiRestaurantLoyaltyService, LoyaltyValidationService

logger = logging.getLogger(__name__)

class MultiRestaurantLoyaltyViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """
    ViewSet for multi-restaurant loyalty program operations
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CustomerLoyaltySerializer
    
    def get_queryset(self):
        return CustomerLoyalty.objects.filter(customer=self.request.user.customer_profile)
    
    def get_serializer_class(self):
        if self.action == 'restaurant_status':
            return RestaurantLoyaltySettingsSerializer
        elif self.action == 'restaurant_rewards':
            return RewardSerializer
        elif self.action == 'redeem_at_restaurant':
            return PointsRedemptionSerializer
        elif self.action == 'referral':
            return ReferralSerializer
        return super().get_serializer_class()
    
    @action(detail=False, methods=['get'])
    def points(self, request):
        """
        Get current points balance and loyalty status
        """
        try:
            loyalty_profile = self.get_object()
            if not loyalty_profile:
                return Response({
                    'error': 'Loyalty profile not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = self.get_serializer(loyalty_profile)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Error retrieving points balance: {str(e)}")
            return Response({
                'error': 'Unable to retrieve points balance'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def restaurant_status(self, request):
        """
        Get loyalty program status for a specific restaurant
        """
        restaurant_id = request.query_params.get('restaurant_id')
        if not restaurant_id:
            return Response({
                'error': 'restaurant_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            restaurant = Restaurant.objects.get(pk=restaurant_id)
            customer = request.user.customer_profile
            
            loyalty_status = MultiRestaurantLoyaltyService.get_customer_loyalty_status(customer, restaurant)
            
            if loyalty_status is None:
                return Response({
                    'error': 'Unable to determine loyalty status for this restaurant'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            response_data = {
                'restaurant_id': restaurant.restaurant_id,
                'restaurant_name': restaurant.name,
                'is_enrolled': loyalty_status['is_enrolled'],
                'program': MultiRestaurantLoyaltyProgramSerializer(loyalty_status['program']).data if loyalty_status['program'] else None
            }
            
            if loyalty_status['is_enrolled']:
                loyalty_serializer = CustomerLoyaltySerializer(
                    loyalty_status['loyalty_profile'],
                    context={'restaurant': restaurant}
                )
                response_data.update(loyalty_serializer.data)
            
            return Response(response_data)
        
        except Restaurant.DoesNotExist:
            return Response({
                'error': 'Restaurant not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error checking restaurant status: {str(e)}")
            return Response({
                'error': 'Unable to check restaurant loyalty status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def enroll(self, request):
        """
        Enroll customer in loyalty program for a specific restaurant
        """
        restaurant_id = request.data.get('restaurant_id')
        if not restaurant_id:
            return Response({
                'error': 'restaurant_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            restaurant = Restaurant.objects.get(pk=restaurant_id)
            customer = request.user.customer_profile
            
            success, result = MultiRestaurantLoyaltyService.enroll_customer_in_program(customer, restaurant)
            
            if success:
                serializer = CustomerLoyaltySerializer(result)
                return Response({
                    'message': f'Successfully enrolled in loyalty program at {restaurant.name}',
                    'loyalty_profile': serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': result
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Restaurant.DoesNotExist:
            return Response({
                'error': 'Restaurant not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error enrolling customer: {str(e)}")
            return Response({
                'error': 'Unable to enroll in loyalty program'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def restaurant_rewards(self, request):
        """
        Get available rewards for a specific restaurant
        """
        restaurant_id = request.query_params.get('restaurant_id')
        if not restaurant_id:
            return Response({
                'error': 'restaurant_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            restaurant = Restaurant.objects.get(pk=restaurant_id)
            customer = request.user.customer_profile
            
            available_rewards = MultiRestaurantLoyaltyService.get_available_rewards_for_restaurant(customer, restaurant)
            
            serializer = RewardSerializer(available_rewards, many=True)
            return Response({
                'restaurant_id': restaurant.restaurant_id,
                'restaurant_name': restaurant.name,
                'rewards': serializer.data,
                'total_rewards': len(available_rewards)
            })
        
        except Restaurant.DoesNotExist:
            return Response({
                'error': 'Restaurant not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting restaurant rewards: {str(e)}")
            return Response({
                'error': 'Unable to retrieve rewards for this restaurant'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def my_restaurants(self, request):
        """
        Get all restaurants where the customer has loyalty activity
        """
        try:
            customer = request.user.customer_profile
            loyalty_profiles = CustomerLoyalty.objects.filter(customer=customer)
            
            restaurant_data = []
            for profile in loyalty_profiles:
                for restaurant_id, stats in profile.restaurant_stats.items():
                    try:
                        restaurant = Restaurant.objects.get(pk=restaurant_id)
                        restaurant_data.append({
                            'restaurant_id': restaurant.restaurant_id,
                            'restaurant_name': restaurant.name,
                            'program_name': profile.program.name,
                            'program_type': profile.program.program_type,
                            'orders': stats['orders'],
                            'total_spent': stats['spent'],
                            'last_order': stats['last_order'],
                            'current_tier': profile.tier,
                            'current_points': profile.current_points,
                        })
                    except Restaurant.DoesNotExist:
                        continue
            
            restaurant_data.sort(key=lambda x: x['last_order'] or '', reverse=True)
            
            return Response({
                'restaurants': restaurant_data,
                'total_restaurants': len(restaurant_data)
            })
        
        except Exception as e:
            logger.error(f"Error getting customer restaurants: {str(e)}")
            return Response({
                'error': 'Unable to retrieve restaurant loyalty data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def redeem_at_restaurant(self, request):
        """
        Redeem points for a reward at a specific restaurant
        """
        try:
            serializer = PointsRedemptionSerializer(data=request.data, context={'request': request})
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            restaurant_id = request.data.get('restaurant_id')
            reward_id = request.data.get('reward_id')
            
            if not restaurant_id:
                return Response({
                    'error': 'restaurant_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            restaurant = Restaurant.objects.get(pk=restaurant_id)
            customer = request.user.customer_profile
            
            program = MultiRestaurantLoyaltyService.get_default_program_for_restaurant(restaurant)
            if not program:
                return Response({
                    'error': 'No loyalty program available for this restaurant'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                loyalty_profile = customer.loyalty_profile.get(program=program)
                reward = serializer.validated_data['reward']
                
                success, result = MultiRestaurantLoyaltyService.redeem_points_for_reward(
                    loyalty_profile, reward, restaurant
                )
                
                if success:
                    redemption_serializer = RewardRedemptionSerializer(result)
                    return Response(redemption_serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'error': result
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except CustomerLoyalty.DoesNotExist:
                return Response({
                    'error': 'You are not enrolled in the loyalty program for this restaurant'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Restaurant.DoesNotExist:
            return Response({
                'error': 'Restaurant not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error redeeming reward at restaurant: {str(e)}")
            return Response({
                'error': 'Unable to process redemption'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """
        Get points transaction history
        """
        try:
            loyalty_profiles = self.get_queryset()
            transactions = PointsTransaction.objects.filter(
                customer_loyalty__in=loyalty_profiles
            ).order_by('-transaction_date')[:50]
            
            serializer = PointsTransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Error retrieving transactions: {str(e)}")
            return Response({
                'error': 'Unable to retrieve transaction history'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def redemptions(self, request):
        """
        Get reward redemption history
        """
        try:
            loyalty_profiles = self.get_queryset()
            redemptions = RewardRedemption.objects.filter(
                customer_loyalty__in=loyalty_profiles
            ).order_by('-created_at')
            
            serializer = RewardRedemptionSerializer(redemptions, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Error retrieving redemptions: {str(e)}")
            return Response({
                'error': 'Unable to retrieve redemption history'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def referral(self, request):
        """
        Process referral signup
        """
        try:
            loyalty_profile = self.get_object()
            if not loyalty_profile:
                return Response({
                    'error': 'Loyalty profile not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = ReferralSerializer(data=request.data, context={'request': request})
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            referred_email = serializer.validated_data['email']
            
            # Use the complete referral service
            success, result = LoyaltyService.process_referral(loyalty_profile, referred_email)
            
            if success:
                return Response({
                    'message': 'Referral invitation sent successfully!',
                    'referral_id': result.referral_id,
                    'referred_email': referred_email,
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': result
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error processing referral: {str(e)}")
            return Response({
                'error': 'Unable to process referral invitation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def referral_stats(self, request):
        """
        Get referral statistics for the current user
        """
        try:
            loyalty_profile = self.get_object()
            if not loyalty_profile:
                return Response({
                    'error': 'Loyalty profile not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            from ..models import Referral
            customer = loyalty_profile.customer
            
            total_referrals = Referral.objects.filter(referrer=customer).count()
            completed_referrals = Referral.objects.filter(referrer=customer, status='completed').count()
            pending_referrals = Referral.objects.filter(referrer=customer, status='pending').count()
            
            program = loyalty_profile.program
            potential_points = pending_referrals * program.global_referral_bonus_points
            earned_points = completed_referrals * program.global_referral_bonus_points
            
            return Response({
                'total_referrals': total_referrals,
                'completed_referrals': completed_referrals,
                'pending_referrals': pending_referrals,
                'referral_bonus_points': program.global_referral_bonus_points,
                'potential_points': potential_points,
                'earned_points': earned_points,
                'referral_code': loyalty_profile.referral_code,
            })
        
        except Exception as e:
            logger.error(f"Error getting referral stats: {str(e)}")
            return Response({
                'error': 'Unable to retrieve referral statistics'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def referral_history(self, request):
        """
        Get referral history for the current user
        """
        try:
            loyalty_profile = self.get_object()
            if not loyalty_profile:
                return Response({
                    'error': 'Loyalty profile not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            from ..models import Referral
            customer = loyalty_profile.customer
            referrals = Referral.objects.filter(referrer=customer).order_by('-created_at')
            
            referral_data = []
            for referral in referrals:
                referral_data.append({
                    'referral_id': referral.referral_id,
                    'referred_email': referral.referred_email,
                    'status': referral.status,
                    'created_at': referral.created_at,
                    'completed_at': referral.completed_at,
                    'expires_at': referral.expires_at,
                    'is_expired': referral.is_expired(),
                })
            
            return Response({
                'referrals': referral_data,
                'total_count': len(referral_data)
            })
        
        except Exception as e:
            logger.error(f"Error getting referral history: {str(e)}")
            return Response({
                'error': 'Unable to retrieve referral history'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def validate_redemption(self, request):
        """
        Validate if a reward can be redeemed without actually redeeming it
        """
        try:
            restaurant_id = request.data.get('restaurant_id')
            reward_id = request.data.get('reward_id')
            
            if not restaurant_id or not reward_id:
                return Response({
                    'error': 'restaurant_id and reward_id are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            restaurant = Restaurant.objects.get(pk=restaurant_id)
            customer = request.user.customer_profile
            
            program = MultiRestaurantLoyaltyService.get_default_program_for_restaurant(restaurant)
            if not program:
                return Response({
                    'error': 'No loyalty program available for this restaurant'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                loyalty_profile = customer.loyalty_profile.get(program=program)
                reward = Reward.objects.get(pk=reward_id, program=program)
                
                is_valid, errors = LoyaltyValidationService.validate_reward_redemption(
                    loyalty_profile, reward, restaurant
                )
                
                return Response({
                    'can_redeem': is_valid,
                    'errors': errors,
                    'reward_name': reward.name,
                    'points_required': reward.points_required,
                    'current_points': loyalty_profile.current_points
                })
                
            except CustomerLoyalty.DoesNotExist:
                return Response({
                    'can_redeem': False,
                    'errors': ['You are not enrolled in the loyalty program for this restaurant']
                })
            except Reward.DoesNotExist:
                return Response({
                    'can_redeem': False,
                    'errors': ['Reward not found for this restaurant']
                })
        
        except Restaurant.DoesNotExist:
            return Response({
                'can_redeem': False,
                'errors': ['Restaurant not found']
            })
        except Exception as e:
            logger.error(f"Error validating redemption: {str(e)}")
            return Response({
                'can_redeem': False,
                'errors': ['Unable to validate redemption']
            })

class RewardViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    ViewSet for browsing rewards
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RewardSerializer
    queryset = Reward.objects.filter(is_active=True)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by current user's loyalty program
        try:
            loyalty_profile = self.request.user.customer_profile.loyalty_profile
            queryset = queryset.filter(program=loyalty_profile.program)
        except CustomerLoyalty.DoesNotExist:
            return Reward.objects.none()
        
        # Filter by restaurant if provided
        restaurant_id = self.request.query_params.get('restaurant_id')
        if restaurant_id:
            try:
                from ..models import Restaurant
                restaurant = Restaurant.objects.get(pk=restaurant_id)
                queryset = queryset.filter(
                    models.Q(restaurant=restaurant) | 
                    models.Q(restaurant__isnull=True) |
                    models.Q(applicable_restaurants=restaurant)
                ).distinct()
            except Restaurant.DoesNotExist:
                return Reward.objects.none()
        
        # Filter by availability
        queryset = queryset.filter(
            valid_from__lte=timezone.now()
        ).filter(
            models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=timezone.now())
        )
        
        return queryset