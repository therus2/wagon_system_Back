"""
Команда для очистки вагонов, которые находятся в составе более 90 дней.
Удаляет вагоны из базы данных, если они были включены в состав более 90 дней назад.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from wagons.models import Wagon


class Command(BaseCommand):
    help = 'Удаляет вагоны, которые находятся в составе более 90 дней'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, какие вагоны будут удалены, без фактического удаления',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Количество дней в составе перед удалением (по умолчанию: 90)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']
        
        # Вычисляем дату, до которой вагоны должны быть удалены
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Находим вагоны в составе старше указанного количества дней
        old_wagons = Wagon.objects.filter(
            in_consist=True,
            in_consist_at__lt=cutoff_date
        )
        
        count = old_wagons.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'Нет вагонов в составе старше {days} дней')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'РЕЖИМ ПРОСМОТРА: Найдено {count} вагонов для удаления:'
                )
            )
            for wagon in old_wagons[:10]:  # Показываем первые 10
                self.stdout.write(
                    f'  - {wagon.wagon_number} (в составе с {wagon.in_consist_at})'
                )
            if count > 10:
                self.stdout.write(f'  ... и ещё {count - 10} вагонов')
        else:
            # Удаляем вагоны
            wagon_numbers = list(old_wagons.values_list('wagon_number', flat=True))
            deleted_count, _ = old_wagons.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Успешно удалено {deleted_count} вагонов из состава:'
                )
            )
            for wagon_number in wagon_numbers[:10]:
                self.stdout.write(f'  - {wagon_number}')
            if len(wagon_numbers) > 10:
                self.stdout.write(f'  ... и ещё {len(wagon_numbers) - 10} вагонов')
