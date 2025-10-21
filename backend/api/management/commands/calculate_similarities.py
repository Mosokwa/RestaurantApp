# Create management/commands/calculate_similarities.py
from django.core.management.base import BaseCommand
from api.recommendation_engine import RecommendationEngine
from api.models import MenuItem, SimilarityMatrix

class Command(BaseCommand):
    help = 'Calculate similarity matrix for recommendations'
    
    def handle(self, *args, **options):
        engine = RecommendationEngine()
        
        self.stdout.write('Calculating menu item similarities...')
        menu_items = MenuItem.objects.filter(is_available=True)
        
        # This would be optimized in production to use batch processing
        for i, item1 in enumerate(menu_items):
            for j, item2 in enumerate(menu_items):
                if i < j:  # Avoid duplicate calculations
                    similarity = engine.calculate_item_similarity(item1, item2, 'menu_item')
                    if similarity > engine.min_similarity_threshold:
                        # Store in SimilarityMatrix
                        SimilarityMatrix.objects.update_or_create(
                            matrix_type='menu_items',
                            item_a_id=item1.item_id,
                            item_b_id=item2.item_id,
                            defaults={
                                'similarity_score': similarity,
                                'calculation_method': 'cosine_similarity'
                            }
                        )
        
        self.stdout.write(self.style.SUCCESS('Similarity matrix calculation completed'))