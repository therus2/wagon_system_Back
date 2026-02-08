from rest_framework import permissions


class IsDispatcherOrAdmin(permissions.BasePermission):
    """Разрешение для диспетчеров и администраторов"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Проверяем роль через группы или кастомное поле
        # Предполагаем, что роли хранятся в группах или в профиле пользователя
        user_groups = request.user.groups.values_list('name', flat=True)
        return 'DISPATCHER' in user_groups or 'ADMIN' in user_groups or request.user.is_staff


class IsComposer(permissions.BasePermission):
    """Разрешение для составителей"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_groups = request.user.groups.values_list('name', flat=True)
        return 'COMPOSER' in user_groups or request.user.is_staff


class IsAdmin(permissions.BasePermission):
    """Разрешение только для администраторов"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_staff
