from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import (
    StationConfig, WagonType, CargoType, CisternType, Conductor, Firm, Wagon
)


@admin.register(StationConfig)
class StationConfigAdmin(admin.ModelAdmin):
    """Админка для конфигурации станции (singleton)"""
    list_display = ['tracks_count', 'created_at']
    
    def has_add_permission(self, request):
        """Запрещает создание нескольких записей"""
        if StationConfig.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        """Запрещает удаление единственной записи"""
        return False


@admin.register(WagonType)
class WagonTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active']


@admin.register(CargoType)
class CargoTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'hazard_class', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active', 'hazard_class']


@admin.register(CisternType)
class CisternTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active']


@admin.register(Conductor)
class ConductorAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active']


@admin.register(Firm)
class FirmAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'is_active']
    search_fields = ['name', 'country']
    list_filter = ['is_active', 'country']


@admin.register(Wagon)
class WagonAdmin(admin.ModelAdmin):
    list_display = [
        'wagon_number', 'wagon_type', 'firm', 'path_number', 
        'position', 'condition_status', 'is_operational', 'can_roll_from_hill', 'created_at'
    ]
    search_fields = ['wagon_number', 'wagon_type__name']
    list_filter = ['wagon_type', 'condition_status', 'is_operational', 'can_roll_from_hill', 'path_number']
    readonly_fields = ['created_at', 'created_by']
    
    def save_model(self, request, obj, form, change):
        if not change:  # При создании
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
