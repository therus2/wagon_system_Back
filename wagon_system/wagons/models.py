from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class StationConfig(models.Model):
    """Конфигурация станции (singleton)"""
    tracks_count = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Количество путей"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Конфигурация станции"
        verbose_name_plural = "Конфигурация станции"

    def save(self, *args, **kwargs):
        """Гарантирует единственную запись (singleton)"""
        if not self.pk and StationConfig.objects.exists():
            raise ValidationError("Может существовать только одна конфигурация станции")
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Конфигурация станции: {self.tracks_count} путей"


class WagonType(models.Model):
    """Справочник типов вагонов"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Тип вагона"
        verbose_name_plural = "Типы вагонов"
        ordering = ['name']

    def __str__(self):
        return self.name


class CargoType(models.Model):
    """Справочник типов грузов"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    hazard_class = models.CharField(max_length=50, null=True, blank=True, verbose_name="Класс опасности")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Тип груза"
        verbose_name_plural = "Типы грузов"
        ordering = ['name']

    def __str__(self):
        return self.name


class CisternType(models.Model):
    """Справочник типов цистерн"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Тип цистерны"
        verbose_name_plural = "Типы цистерн"
        ordering = ['name']

    def __str__(self):
        return self.name


class Conductor(models.Model):
    """Справочник проводников (охранники, полиция и т.д.)"""
    name = models.CharField(max_length=255, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Проводник"
        verbose_name_plural = "Проводники"
        ordering = ['name']

    def __str__(self):
        return self.name


class Firm(models.Model):
    """Справочник фирм"""
    name = models.CharField(max_length=200, verbose_name="Название")
    country = models.CharField(max_length=100, verbose_name="Страна")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Фирма"
        verbose_name_plural = "Фирмы"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.country})"


class Wagon(models.Model):
    """Модель вагона"""
    CONDITION_CHOICES = [
        ('OK', 'Исправен'),
        ('MINOR', 'Незначительные неисправности'),
        ('MAJOR', 'Значительные неисправности'),
        ('OUT_OF_SERVICE', 'Не пригоден к эксплуатации'),
    ]

    wagon_number = models.CharField(max_length=50, unique=True, verbose_name="Номер вагона")
    wagon_type = models.ForeignKey(WagonType, on_delete=models.PROTECT, verbose_name="Тип вагона")
    firm = models.ForeignKey(Firm, on_delete=models.PROTECT, verbose_name="Фирма")
    path_number = models.IntegerField(verbose_name="Номер пути")
    position = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Позиция на пути"
    )
    length = models.FloatField(
        validators=[MinValueValidator(0.1)],
        verbose_name="Длина (м)"
    )
    height = models.FloatField(
        validators=[MinValueValidator(0.1)],
        verbose_name="Высота (м)"
    )
    load_capacity = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.1)],
        verbose_name="Грузоподъёмность (т)"
    )
    # Новые поля
    axle_count = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name="Количество осей"
    )
    net_weight = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.1)],
        verbose_name="Масса нетто (кг)"
    )
    wagon_weight = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.1)],
        verbose_name="Масса вагона (кг)"
    )
    body_volume = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.1)],
        verbose_name="Объём кузова (м³)"
    )
    # Специфика цистерн
    fill_height = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.1)],
        verbose_name="Высота налива (см)"
    )
    cistern_type = models.ForeignKey(
        'CisternType',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Тип цистерны"
    )
    # Проводники (охранники, полиция и т.д.)
    conductors = models.ForeignKey(
        'Conductor',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Проводники"
    )
    # Можно ли вагон скатывать с горки
    can_roll_from_hill = models.BooleanField(
        default=True,
        verbose_name="Можно скатывать с горки"
    )
    arrived_at = models.DateTimeField(verbose_name="Дата и время прибытия")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Создал")
    condition_status = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='OK',
        verbose_name="Техническое состояние"
    )
    is_operational = models.BooleanField(default=True, verbose_name="Готов к эксплуатации")
    # Статус в составе
    in_consist = models.BooleanField(default=False, verbose_name="Находится в составе")
    in_consist_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата включения в состав")
    comment = models.TextField(null=True, blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    @property
    def gross_weight(self):
        """Масса брутто (нетто + масса вагона)"""
        if self.net_weight is not None and self.wagon_weight is not None:
            return self.net_weight + self.wagon_weight
        return None

    class Meta:
        verbose_name = "Вагон"
        verbose_name_plural = "Вагоны"
        ordering = ['path_number', 'position']

    def clean(self):
        """Валидация path_number относительно tracks_count"""
        try:
            config = StationConfig.objects.first()
            if config and self.path_number > config.tracks_count:
                raise ValidationError(
                    f"Номер пути ({self.path_number}) не может превышать количество путей ({config.tracks_count})"
                )
        except StationConfig.DoesNotExist:
            pass

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.wagon_number} (Путь {self.path_number}, Позиция {self.position})"
