# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagons', '0002_remove_cargo_types_add_new_fields'),
    ]

    operations = [
        # Создаем модели CisternType и Conductor
        migrations.CreateModel(
            name='CisternType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Название')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
            ],
            options={
                'verbose_name': 'Тип цистерны',
                'verbose_name_plural': 'Типы цистерн',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Conductor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Название')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
            ],
            options={
                'verbose_name': 'Проводник',
                'verbose_name_plural': 'Проводники',
                'ordering': ['name'],
            },
        ),
        # Удаляем ManyToMany поле climate_conditions
        migrations.RemoveField(
            model_name='wagon',
            name='climate_conditions',
        ),
        # Изменяем cistern_type с CharField на ForeignKey
        migrations.AlterField(
            model_name='wagon',
            name='cistern_type',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='wagons.CisternType',
                verbose_name='Тип цистерны'
            ),
        ),
        # Изменяем conductors с CharField на ForeignKey
        migrations.AlterField(
            model_name='wagon',
            name='conductors',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='wagons.Conductor',
                verbose_name='Проводники'
            ),
        ),
        # Добавляем can_roll_from_hill
        migrations.AddField(
            model_name='wagon',
            name='can_roll_from_hill',
            field=models.BooleanField(default=True, verbose_name='Можно скатывать с горки'),
        ),
    ]
