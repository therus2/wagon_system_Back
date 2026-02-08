# Generated manually

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('wagons', '0001_initial'),
    ]

    operations = [
        # Удаляем ManyToMany поле cargo_types
        migrations.RemoveField(
            model_name='wagon',
            name='cargo_types',
        ),
        # Переименовываем max_load_weight в load_capacity
        migrations.RenameField(
            model_name='wagon',
            old_name='max_load_weight',
            new_name='load_capacity',
        ),
        # Добавляем новые поля
        migrations.AddField(
            model_name='wagon',
            name='axle_count',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Количество осей'),
        ),
        migrations.AddField(
            model_name='wagon',
            name='net_weight',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.1)], verbose_name='Масса нетто (кг)'),
        ),
        migrations.AddField(
            model_name='wagon',
            name='wagon_weight',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.1)], verbose_name='Масса вагона (кг)'),
        ),
        migrations.AddField(
            model_name='wagon',
            name='body_volume',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.1)], verbose_name='Объём кузова (м³)'),
        ),
        migrations.AddField(
            model_name='wagon',
            name='fill_height',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.1)], verbose_name='Высота налива (см)'),
        ),
        migrations.AddField(
            model_name='wagon',
            name='cistern_type',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Тип цистерны'),
        ),
        migrations.AddField(
            model_name='wagon',
            name='conductors',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Проводники'),
        ),
        migrations.AddField(
            model_name='wagon',
            name='in_consist',
            field=models.BooleanField(default=False, verbose_name='Находится в составе'),
        ),
        migrations.AddField(
            model_name='wagon',
            name='in_consist_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата включения в состав'),
        ),
    ]
