# management/commands/sync_pos_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import POSConnection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync POS data for all active connections'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--connection-id',
            type=int,
            help='Sync specific connection only'
        )
        parser.add_argument(
            '--sync-type',
            type=str,
            choices=['menu', 'inventory', 'all'],
            default='all',
            help='Type of sync to perform'
        )
    
    def handle(self, *args, **options):
        connection_id = options.get('connection_id')
        sync_type = options.get('sync_type')
        
        if connection_id:
            connections = POSConnection.objects.filter(
                connection_id=connection_id,
                is_active=True
            )
        else:
            connections = POSConnection.objects.filter(
                is_active=True,
                sync_status='connected'
            )
        
        for connection in connections:
            self.stdout.write(f"Syncing {connection.connection_name}...")
            
            try:
                if sync_type in ['menu', 'all'] and connection.auto_sync_menu:
                    success, stats = connection.sync_menu_items()
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Menu sync successful: {stats}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Menu sync failed: {stats}"
                            )
                        )
                
                if sync_type in ['inventory', 'all'] and connection.auto_sync_inventory:
                    success, stats = connection.sync_inventory()
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Inventory sync successful: {stats}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Inventory sync failed: {stats}"
                            )
                        )
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error syncing {connection.connection_name}: {str(e)}"
                    )
                )
                logger.error(f"POS sync error: {str(e)}")