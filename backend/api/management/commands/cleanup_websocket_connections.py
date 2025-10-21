from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.models import WebSocketConnection


class Command(BaseCommand):
    help = 'Clean up stale WebSocket connections'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Hours after which inactive connections are considered stale'
        )
    
    def handle(self, *args, **options):
        hours = options['hours']
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Find stale connections (active but no recent activity)
        stale_connections = WebSocketConnection.objects.filter(
            is_active=True,
            last_activity__lt=cutoff_time
        )
        
        count = stale_connections.count()
        
        if count > 0:
            self.stdout.write(f'Found {count} stale WebSocket connections')
            
            # Disconnect stale connections
            for connection in stale_connections:
                connection.disconnect()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully disconnected {count} stale connections')
            )
        else:
            self.stdout.write('No stale WebSocket connections found')