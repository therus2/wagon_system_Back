from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    StationConfig, WagonType, CargoType, CisternType, Conductor, Firm, Wagon
)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя"""
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role']
        read_only_fields = ['id']
    
    def get_role(self, obj):
        """Получить роль пользователя из групп"""
        groups = obj.groups.values_list('name', flat=True)
        if 'ADMIN' in groups or obj.is_staff:
            return 'ADMIN'
        elif 'DISPATCHER' in groups:
            return 'DISPATCHER'
        elif 'COMPOSER' in groups:
            return 'COMPOSER'
        return None


class WagonTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WagonType
        fields = '__all__'


class CargoTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoType
        fields = '__all__'


class CisternTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CisternType
        fields = '__all__'


class ConductorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conductor
        fields = '__all__'


class FirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Firm
        fields = '__all__'


class StationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = StationConfig
        fields = '__all__'
        read_only_fields = ['created_at']


class WagonSerializer(serializers.ModelSerializer):
    """Сериализатор для вагона"""
    wagon_type = WagonTypeSerializer(read_only=True)
    firm = FirmSerializer(read_only=True)
    cistern_type = CisternTypeSerializer(read_only=True)
    conductors = ConductorSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    gross_weight = serializers.ReadOnlyField()
    
    # Write-only поля для создания/обновления
    wagon_type_id = serializers.IntegerField(write_only=True)
    firm_id = serializers.IntegerField(write_only=True)
    cistern_type_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    conductors_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Wagon
        fields = [
            'id', 'wagon_number', 'wagon_type', 'wagon_type_id',
            'firm', 'firm_id', 'path_number', 'position', 'length', 'height',
            'load_capacity', 'axle_count', 'net_weight', 'wagon_weight',
            'gross_weight', 'body_volume', 'fill_height', 'cistern_type', 'cistern_type_id',
            'conductors', 'conductors_id', 'can_roll_from_hill',
            'arrived_at', 'created_by', 'condition_status',
            'is_operational', 'in_consist', 'in_consist_at',
            'comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'gross_weight']
    
    def validate_path_number(self, value):
        """Валидация номера пути"""
        try:
            config = StationConfig.objects.first()
            if config and value > config.tracks_count:
                raise serializers.ValidationError(
                    f"Номер пути не может превышать {config.tracks_count}"
                )
        except StationConfig.DoesNotExist:
            pass
        return value
    
    def create(self, validated_data):
        """Создание вагона"""
        cistern_type_id = validated_data.pop('cistern_type_id', None)
        conductors_id = validated_data.pop('conductors_id', None)
        wagon_type_id = validated_data.pop('wagon_type_id')
        firm_id = validated_data.pop('firm_id')
        
        validated_data['wagon_type_id'] = wagon_type_id
        validated_data['firm_id'] = firm_id
        if cistern_type_id:
            validated_data['cistern_type_id'] = cistern_type_id
        if conductors_id:
            validated_data['conductors_id'] = conductors_id
        validated_data['created_by'] = self.context['request'].user
        
        wagon = Wagon.objects.create(**validated_data)
        return wagon
    
    def update(self, instance, validated_data):
        """Обновление вагона"""
        cistern_type_id = validated_data.pop('cistern_type_id', None)
        conductors_id = validated_data.pop('conductors_id', None)
        wagon_type_id = validated_data.pop('wagon_type_id', None)
        firm_id = validated_data.pop('firm_id', None)
        
        if wagon_type_id:
            validated_data['wagon_type_id'] = wagon_type_id
        if firm_id:
            validated_data['firm_id'] = firm_id
        if cistern_type_id is not None:
            validated_data['cistern_type_id'] = cistern_type_id
        if conductors_id is not None:
            validated_data['conductors_id'] = conductors_id
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class ComposeItemSerializer(serializers.Serializer):
    """Сериализатор для элемента требования к составу (только параметры фильтрации)"""
    wagon_type = serializers.IntegerField()
    count = serializers.IntegerField(min_value=1)
    # Опциональные параметры фильтрации
    firm = serializers.IntegerField(required=False, allow_null=True)
    load_capacity_min = serializers.FloatField(min_value=0.1, required=False, allow_null=True)
    load_capacity_max = serializers.FloatField(min_value=0.1, required=False, allow_null=True)
    axle_count = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    wagon_weight_min = serializers.FloatField(min_value=0.1, required=False, allow_null=True)
    wagon_weight_max = serializers.FloatField(min_value=0.1, required=False, allow_null=True)
    can_roll_from_hill = serializers.BooleanField(required=False, allow_null=True)
    condition_status = serializers.ChoiceField(
        choices=['OK', 'MINOR', 'MAJOR', 'OUT_OF_SERVICE'],
        required=False,
        allow_null=True
    )
    body_volume_min = serializers.FloatField(min_value=0.1, required=False, allow_null=True)
    body_volume_max = serializers.FloatField(min_value=0.1, required=False, allow_null=True)
    # Параметры для цистерн
    cistern_type_id = serializers.IntegerField(required=False, allow_null=True)
    fill_height_min = serializers.FloatField(min_value=0.1, required=False, allow_null=True)
    fill_height_max = serializers.FloatField(min_value=0.1, required=False, allow_null=True)


class ComposeRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса подбора состава"""
    items = ComposeItemSerializer(many=True)
    max_total_length = serializers.FloatField(min_value=0.1, required=False, allow_null=True)
    # Параметры сопровождения состава (не для фильтрации)
    conductors_id = serializers.IntegerField(required=False, allow_null=True, help_text="Проводники, сопровождающие состав")


class BulkWagonSerializer(serializers.Serializer):
    """Сериализатор для массового создания вагонов"""
    wagons = WagonSerializer(many=True)


class EditableWagonDataSerializer(serializers.Serializer):
    """Сериализатор для отредактированных данных вагона (только для PDF)"""
    id = serializers.IntegerField(required=False, allow_null=True)
    position = serializers.IntegerField()
    path_number = serializers.IntegerField()
    wagon_position = serializers.IntegerField()
    wagon_number = serializers.CharField()
    wagon_type = serializers.CharField()
    load_capacity = serializers.FloatField(required=False, allow_null=True)
    axle_count = serializers.IntegerField(required=False, allow_null=True)
    net_weight = serializers.FloatField(required=False, allow_null=True)
    wagon_weight = serializers.FloatField(required=False, allow_null=True)
    gross_weight = serializers.FloatField(required=False, allow_null=True)
    conductors = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    body_volume = serializers.FloatField(required=False, allow_null=True)
    fill_height = serializers.FloatField(required=False, allow_null=True)
    cistern_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class ComposeSaveSerializer(serializers.Serializer):
    """Сериализатор для сохранения состава"""
    wagon_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    # Параметры сопровождения состава
    conductors_id = serializers.IntegerField(required=False, allow_null=True, help_text="Проводники, сопровождающие состав")
    # Отредактированные данные вагонов (только для PDF, не сохраняются в БД)
    edited_wagons_data = EditableWagonDataSerializer(many=True, required=False, allow_null=True)