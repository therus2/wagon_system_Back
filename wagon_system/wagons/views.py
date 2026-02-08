from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Case, When, Value, IntegerField
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from .models import (
    StationConfig, WagonType, CargoType, CisternType, Conductor, Firm, Wagon
)
from .serializers import (
    StationConfigSerializer, WagonTypeSerializer, CargoTypeSerializer,
    CisternTypeSerializer, ConductorSerializer, FirmSerializer, WagonSerializer,
    ComposeRequestSerializer, BulkWagonSerializer, ComposeSaveSerializer
)
from .permissions import IsDispatcherOrAdmin, IsComposer, IsAdmin


class StationConfigViewSet(viewsets.ModelViewSet):
    """ViewSet для конфигурации станции"""
    queryset = StationConfig.objects.all()
    serializer_class = StationConfigSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """PUT только для администраторов"""
        if self.action == 'update' or self.action == 'partial_update':
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def list(self, request, *args, **kwargs):
        """Возвращает единственную запись"""
        config = StationConfig.objects.first()
        if config:
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        return Response({'detail': 'Конфигурация не найдена'}, status=status.HTTP_404_NOT_FOUND)


class WagonTypeViewSet(viewsets.ModelViewSet):
    """ViewSet для типов вагонов"""
    queryset = WagonType.objects.filter(is_active=True)
    serializer_class = WagonTypeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """POST, PUT, DELETE только для диспетчеров и администраторов"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsDispatcherOrAdmin()]
        return [IsAuthenticated()]


class CargoTypeViewSet(viewsets.ModelViewSet):
    """ViewSet для типов грузов"""
    queryset = CargoType.objects.filter(is_active=True)
    serializer_class = CargoTypeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsDispatcherOrAdmin()]
        return [IsAuthenticated()]


class CisternTypeViewSet(viewsets.ModelViewSet):
    """ViewSet для типов цистерн"""
    queryset = CisternType.objects.filter(is_active=True)
    serializer_class = CisternTypeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsDispatcherOrAdmin()]
        return [IsAuthenticated()]


class ConductorViewSet(viewsets.ModelViewSet):
    """ViewSet для проводников"""
    queryset = Conductor.objects.filter(is_active=True)
    serializer_class = ConductorSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsDispatcherOrAdmin()]
        return [IsAuthenticated()]


class FirmViewSet(viewsets.ModelViewSet):
    """ViewSet для фирм"""
    queryset = Firm.objects.filter(is_active=True)
    serializer_class = FirmSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsDispatcherOrAdmin()]
        return [IsAuthenticated()]


class WagonViewSet(viewsets.ModelViewSet):
    """ViewSet для вагонов"""
    queryset = Wagon.objects.all()
    serializer_class = WagonSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Фильтрация вагонов"""
        queryset = Wagon.objects.all()
        
        path = self.request.query_params.get('path', None)
        if path:
            queryset = queryset.filter(path_number=path)
        
        is_operational = self.request.query_params.get('is_operational', None)
        if is_operational is not None:
            is_operational_bool = is_operational.lower() == 'true'
            queryset = queryset.filter(is_operational=is_operational_bool)
        
        in_consist = self.request.query_params.get('in_consist', None)
        if in_consist is not None:
            in_consist_bool = in_consist.lower() == 'true'
            queryset = queryset.filter(in_consist=in_consist_bool)
        
        return queryset.distinct()
    
    def get_permissions(self):
        """POST, PUT, DELETE только для диспетчеров и администраторов"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsDispatcherOrAdmin()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Установка created_by из request.user"""
        serializer.save(created_by=self.request.user)


class BulkWagonCreateView(APIView):
    """API для массового создания вагонов"""
    permission_classes = [IsDispatcherOrAdmin]
    
    def post(self, request):
        serializer = BulkWagonSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        wagons_data = serializer.validated_data['wagons']
        created = []
        errors = []
        
        for idx, wagon_data in enumerate(wagons_data):
            wagon_serializer = WagonSerializer(
                data=wagon_data,
                context={'request': request}
            )
            if wagon_serializer.is_valid():
                wagon = wagon_serializer.save()
                created.append(wagon_serializer.data)
            else:
                errors.append({
                    'index': idx,
                    'errors': wagon_serializer.errors
                })
        
        return Response({
            'created': len(created),
            'failed': len(errors),
            'wagons': created,
            'errors': errors
        }, status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST)


class ComposeView(APIView):
    """API для подбора составов"""
    permission_classes = [IsComposer]
    
    def post(self, request):
        serializer = ComposeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        items = serializer.validated_data['items']
        max_total_length = serializer.validated_data.get('max_total_length')
        
        result_wagons = []
        total_length = 0
        errors = []
        
        # Получаем все операционные вагоны, не в составе
        available_wagons = Wagon.objects.filter(
            is_operational=True,
            in_consist=False
        )
        
        for item in items:
            wagon_type_id = item['wagon_type']
            count = item['count']
            
            # Фильтруем вагоны по базовым требованиям (тип вагона и не в составе)
            filtered = available_wagons.filter(
                wagon_type_id=wagon_type_id,
                in_consist=False
            )
            
            # Фильтр по фирме (только если указан)
            if item.get('firm'):
                filtered = filtered.filter(firm_id=item['firm'])
            
            # Фильтр по грузоподъёмности (диапазон) - более гибкий
            load_capacity_min = item.get('load_capacity_min')
            load_capacity_max = item.get('load_capacity_max')
            if load_capacity_min is not None and load_capacity_max is not None:
                # Оба значения указаны - строгий диапазон
                filtered = filtered.filter(
                    Q(load_capacity__isnull=False) & 
                    Q(load_capacity__gte=load_capacity_min) & 
                    Q(load_capacity__lte=load_capacity_max)
                )
            elif load_capacity_min is not None:
                # Только минимум
                filtered = filtered.filter(
                    Q(load_capacity__isnull=False) & Q(load_capacity__gte=load_capacity_min)
                )
            elif load_capacity_max is not None:
                # Только максимум
                filtered = filtered.filter(
                    Q(load_capacity__isnull=True) | Q(load_capacity__lte=load_capacity_max)
                )
            
            # Фильтр по количеству осей (только если указан)
            if item.get('axle_count'):
                filtered = filtered.filter(axle_count=item['axle_count'])
            
            # Фильтр по массе вагона (диапазон) - более гибкий
            wagon_weight_min = item.get('wagon_weight_min')
            wagon_weight_max = item.get('wagon_weight_max')
            if wagon_weight_min is not None and wagon_weight_max is not None:
                # Оба значения указаны
                filtered = filtered.filter(
                    Q(wagon_weight__isnull=False) & 
                    Q(wagon_weight__gte=wagon_weight_min) & 
                    Q(wagon_weight__lte=wagon_weight_max)
                )
            elif wagon_weight_min is not None:
                filtered = filtered.filter(
                    Q(wagon_weight__isnull=False) & Q(wagon_weight__gte=wagon_weight_min)
                )
            elif wagon_weight_max is not None:
                filtered = filtered.filter(
                    Q(wagon_weight__isnull=True) | Q(wagon_weight__lte=wagon_weight_max)
                )
            
            # Фильтр по массе нетто (диапазон) - более гибкий
            net_weight_min = item.get('net_weight_min')
            net_weight_max = item.get('net_weight_max')
            if net_weight_min is not None and net_weight_max is not None:
                filtered = filtered.filter(
                    Q(net_weight__isnull=False) & 
                    Q(net_weight__gte=net_weight_min) & 
                    Q(net_weight__lte=net_weight_max)
                )
            elif net_weight_min is not None:
                filtered = filtered.filter(
                    Q(net_weight__isnull=False) & Q(net_weight__gte=net_weight_min)
                )
            elif net_weight_max is not None:
                filtered = filtered.filter(
                    Q(net_weight__isnull=True) | Q(net_weight__lte=net_weight_max)
                )
            
            # Фильтр по возможности скатывания с горки (только если указан)
            if item.get('can_roll_from_hill') is not None:
                filtered = filtered.filter(can_roll_from_hill=item['can_roll_from_hill'])
            
            # Фильтр по техническому состоянию (только если указан)
            if item.get('condition_status'):
                filtered = filtered.filter(condition_status=item['condition_status'])
            
            # Фильтр по объёму кузова (диапазон) - более гибкий
            body_volume_min = item.get('body_volume_min')
            body_volume_max = item.get('body_volume_max')
            if body_volume_min is not None and body_volume_max is not None:
                filtered = filtered.filter(
                    Q(body_volume__isnull=False) & 
                    Q(body_volume__gte=body_volume_min) & 
                    Q(body_volume__lte=body_volume_max)
                )
            elif body_volume_min is not None:
                filtered = filtered.filter(
                    Q(body_volume__isnull=False) & Q(body_volume__gte=body_volume_min)
                )
            elif body_volume_max is not None:
                filtered = filtered.filter(
                    Q(body_volume__isnull=True) | Q(body_volume__lte=body_volume_max)
                )
            
            # Фильтры для цистерн (только если указаны)
            if item.get('cistern_type_id'):
                filtered = filtered.filter(cistern_type_id=item['cistern_type_id'])
            
            fill_height_min = item.get('fill_height_min')
            fill_height_max = item.get('fill_height_max')
            if fill_height_min is not None and fill_height_max is not None:
                filtered = filtered.filter(
                    Q(fill_height__isnull=False) & 
                    Q(fill_height__gte=fill_height_min) & 
                    Q(fill_height__lte=fill_height_max)
                )
            elif fill_height_min is not None:
                filtered = filtered.filter(
                    Q(fill_height__isnull=False) & Q(fill_height__gte=fill_height_min)
                )
            elif fill_height_max is not None:
                filtered = filtered.filter(
                    Q(fill_height__isnull=True) | Q(fill_height__lte=fill_height_max)
                )
            
            # Исключаем уже выбранные вагоны
            selected_ids = [w['id'] for w in result_wagons]
            filtered = filtered.exclude(id__in=selected_ids)
            
            # Улучшенная сортировка: приоритет вагонам с заполненными данными
            filtered = filtered.annotate(
                priority=Case(
                    When(load_capacity__isnull=False, wagon_weight__isnull=False, 
                         axle_count__isnull=False, then=Value(1)),
                    When(load_capacity__isnull=False, wagon_weight__isnull=False, then=Value(2)),
                    When(load_capacity__isnull=False, then=Value(3)),
                    default=Value(4),
                    output_field=IntegerField()
                )
            ).order_by('priority', 'path_number', 'position')
            
            # Выбираем первые count вагонов
            filtered_list = list(filtered[:count])
            
            # Если не хватает вагонов, пробуем найти без строгих фильтров (кроме типа)
            if len(filtered_list) < count:
                # Пробуем найти вагоны только по типу (без дополнительных фильтров)
                already_selected = [w['id'] for w in result_wagons]
                # Добавляем ID уже отфильтрованных вагонов
                filtered_ids = [w.id for w in filtered_list]
                all_excluded_ids = already_selected + filtered_ids
                
                fallback_filtered = available_wagons.filter(
                    wagon_type_id=wagon_type_id,
                    in_consist=False
                ).exclude(id__in=all_excluded_ids)
                
                # Сортируем по приоритету
                fallback_filtered = fallback_filtered.annotate(
                    priority=Case(
                        When(load_capacity__isnull=False, wagon_weight__isnull=False, 
                             axle_count__isnull=False, then=Value(1)),
                        When(load_capacity__isnull=False, wagon_weight__isnull=False, then=Value(2)),
                        When(load_capacity__isnull=False, then=Value(3)),
                        default=Value(4),
                        output_field=IntegerField()
                    )
                ).order_by('priority', 'path_number', 'position')
                
                # Берем недостающие вагоны
                needed = count - len(filtered_list)
                fallback_list = list(fallback_filtered[:needed])
                filtered_list.extend(fallback_list)
            
            if len(filtered_list) < count:
                # Получаем название типа вагона для сообщения об ошибке
                try:
                    wagon_type = WagonType.objects.get(id=wagon_type_id)
                    wagon_type_name = wagon_type.name
                except WagonType.DoesNotExist:
                    wagon_type_name = f"тип {wagon_type_id}"
                
                # Подсчитываем общее количество доступных вагонов этого типа
                total_available = available_wagons.filter(
                    wagon_type_id=wagon_type_id,
                    in_consist=False
                ).count()
                
                # Ищем альтернативные вагоны (только по типу, без дополнительных фильтров)
                already_selected = [w['id'] for w in result_wagons]
                alternative_wagons = available_wagons.filter(
                    wagon_type_id=wagon_type_id,
                    in_consist=False
                ).exclude(id__in=already_selected)
                
                # Исключаем уже отобранные в filtered_list
                filtered_ids = [w.id for w in filtered_list]
                alternative_wagons = alternative_wagons.exclude(id__in=filtered_ids)
                
                # Сортируем альтернативы по приоритету
                alternative_wagons = alternative_wagons.annotate(
                    priority=Case(
                        When(load_capacity__isnull=False, wagon_weight__isnull=False, 
                             axle_count__isnull=False, then=Value(1)),
                        When(load_capacity__isnull=False, wagon_weight__isnull=False, then=Value(2)),
                        When(load_capacity__isnull=False, then=Value(3)),
                        default=Value(4),
                        output_field=IntegerField()
                    )
                ).order_by('priority', 'path_number', 'position')[:5]  # Максимум 5 предложений
                
                # Сериализуем альтернативные вагоны
                alternative_data = [WagonSerializer(w).data for w in alternative_wagons]
                
                errors.append({
                    'item': item,
                    'message': f'Недостаточно вагонов типа "{wagon_type_name}". Найдено {len(filtered_list)}, требуется {count}. Всего доступно вагонов этого типа: {total_available}',
                    'alternatives': alternative_data,  # Добавляем предложения
                    'wagon_type_name': wagon_type_name,
                })
                continue
            
            # Проверяем ограничение по длине
            selected_for_item = []
            for wagon in filtered_list:
                if max_total_length and total_length + wagon.length > max_total_length:
                    errors.append({
                        'item': item,
                        'message': f'Превышена максимальная длина состава'
                    })
                    break
                
                wagon_serializer = WagonSerializer(wagon)
                result_wagons.append(wagon_serializer.data)
                selected_for_item.append(wagon)
                total_length += wagon.length
        
        # Вычисляем общую длину
        actual_total_length = sum(w['length'] for w in result_wagons)
        
        return Response({
            'wagons': result_wagons,
            'total_length': actual_total_length,
            'total_count': len(result_wagons),
            'errors': errors
        }, status=status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS)


class ComposeSaveView(APIView):
    """API для сохранения состава и генерации PDF"""
    permission_classes = [IsComposer]
    
    def post(self, request):
        serializer = ComposeSaveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        wagon_ids = serializer.validated_data['wagon_ids']
        conductors_id = serializer.validated_data.get('conductors_id')
        edited_wagons_data = serializer.validated_data.get('edited_wagons_data')
        
        # Загружаем вагоны и сохраняем порядок
        wagons_qs = Wagon.objects.filter(id__in=wagon_ids, in_consist=False)
        wagons_map = {w.id: w for w in wagons_qs}
        ordered_wagons = [wagons_map[wid] for wid in wagon_ids if wid in wagons_map]
        
        if not ordered_wagons:
            return Response({'detail': 'Вагоны не найдены или уже в составе'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Помечаем вагоны как находящиеся в составе
        now = timezone.now()
        Wagon.objects.filter(id__in=[w.id for w in ordered_wagons]).update(
            in_consist=True,
            in_consist_at=now,
        )
        
        # Получаем проводников для состава (если указаны)
        composition_conductors = None
        if conductors_id:
            try:
                composition_conductors = Conductor.objects.get(id=conductors_id)
            except Conductor.DoesNotExist:
                pass
        
        # Создаем словарь отредактированных данных по ID вагона и список по порядку
        edited_data_map = {}  # По ID вагона
        edited_data_list = []  # Список по порядку (для случаев, когда порядок важен)
        if edited_wagons_data:
            for edited_data in edited_wagons_data:
                wagon_id = edited_data.get('id')
                if wagon_id:
                    edited_data_map[wagon_id] = edited_data
                edited_data_list.append(edited_data)
        
        # Генерация PDF
        response = HttpResponse(content_type='application/pdf')
        filename = f"Состав_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Регистрируем кириллический шрифт
        # Используем Arial, так как он точно есть в Windows
        font_path = r"C:\Windows\Fonts\arial.ttf"
        font_bold_path = r"C:\Windows\Fonts\arialbd.ttf"  # Arial Bold
        
        try:
            # Регистрируем обычный шрифт
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont("CustomFont", font_path))
                font_name = "CustomFont"
                
                # Регистрируем жирный шрифт для заголовков
                if os.path.exists(font_bold_path):
                    pdfmetrics.registerFont(TTFont("CustomFont-Bold", font_bold_path))
                else:
                    # Если жирный шрифт не найден, используем обычный для заголовков
                    pdfmetrics.registerFont(TTFont("CustomFont-Bold", font_path))
            else:
                # Если Arial не найден, используем Helvetica
                font_name = 'Helvetica'
        except Exception as e:
            # Если шрифт не найден, откатываемся на Helvetica (но кириллица пропадет)
            print(f"Ошибка регистрации шрифта: {e}")
            font_name = 'Helvetica'
        
        # Создаем PDF документ
        doc = SimpleDocTemplate(response, pagesize=landscape(A4), 
                               leftMargin=10*mm, rightMargin=10*mm,
                               topMargin=15*mm, bottomMargin=15*mm)
        elements = []
        
        # Стили
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#000000'),
            spaceAfter=15,
            alignment=TA_CENTER,
            fontName=font_name,
        )
        
        # Заголовок - используем UTF-8 кодировку
        # ReportLab автоматически обрабатывает Unicode при использовании Paragraph
        title = Paragraph("Состав", title_style)
        elements.append(title)
        elements.append(Spacer(1, 10))
        
        # Подготовка данных таблицы
        table_data = []
        
        # Заголовки колонок (точно как в изображении - без единиц измерения в заголовках)
        # Используем Paragraph для правильной обработки кириллицы
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=7,
            fontName=font_name,
            textColor=colors.white,
            alignment=TA_CENTER,
        )
        headers = [
            Paragraph('№ п/п', header_style),
            Paragraph('№ по расположению', header_style),
            Paragraph('№ вагона', header_style),
            Paragraph('Тип вагона', header_style),
            Paragraph('Грузоподъёмность', header_style),
            Paragraph('Количество осей', header_style),
            Paragraph('Масса нетто', header_style),
            Paragraph('Масса вагона', header_style),
            Paragraph('Масса брутто', header_style),
            Paragraph('Проводники', header_style),
            Paragraph('Объём кузова', header_style),
            Paragraph('Высота налива', header_style),
            Paragraph('Тип цистерны', header_style),
        ]
        table_data.append(headers)
        
        # Данные вагонов
        # Если есть отредактированные данные и их количество совпадает с количеством вагонов,
        # используем их по порядку, иначе пытаемся найти по ID
        use_edited_by_order = (edited_data_list and 
                              len(edited_data_list) == len(ordered_wagons))
        
        for index, wagon in enumerate(ordered_wagons, start=1):
            # Используем отредактированные данные, если они есть, иначе данные из БД
            edited_data = None
            if use_edited_by_order:
                # Используем данные по порядку
                edited_data = edited_data_list[index - 1] if index - 1 < len(edited_data_list) else None
            else:
                # Пытаемся найти по ID
                if edited_data_map:
                    edited_data = edited_data_map.get(wagon.id)
            
            if edited_data:
                # Используем отредактированные данные
                position_num = edited_data.get('position', index)
                path_number = edited_data.get('path_number', wagon.path_number)
                wagon_position = edited_data.get('wagon_position', wagon.position)
                wagon_number = edited_data.get('wagon_number', wagon.wagon_number)
                wagon_type_name = edited_data.get('wagon_type', wagon.wagon_type.name if wagon.wagon_type else '')
                load_capacity = edited_data.get('load_capacity')
                axle_count = edited_data.get('axle_count')
                net_weight = edited_data.get('net_weight')
                wagon_weight = edited_data.get('wagon_weight')
                gross_weight = edited_data.get('gross_weight')
                conductors_name = edited_data.get('conductors', '')
                body_volume = edited_data.get('body_volume')
                fill_height = edited_data.get('fill_height')
                cistern_type_name = edited_data.get('cistern_type', '')
            else:
                # Используем данные из БД
                position_num = index
                path_number = wagon.path_number
                wagon_position = wagon.position
                wagon_number = wagon.wagon_number
                wagon_type_name = wagon.wagon_type.name if wagon.wagon_type else ''
                load_capacity = wagon.load_capacity
                axle_count = wagon.axle_count
                net_weight = wagon.net_weight
                wagon_weight = wagon.wagon_weight
                gross_weight = wagon.gross_weight
                conductors_name = ""
                if composition_conductors:
                    conductors_name = composition_conductors.name
                elif wagon.conductors:
                    conductors_name = wagon.conductors.name
                body_volume = wagon.body_volume
                fill_height = wagon.fill_height
                cistern_type_name = wagon.cistern_type.name if wagon.cistern_type else ''
            
            # Масса брутто
            if gross_weight is None:
                gross_weight_str = "невозможно рассчитать\nмасса нетто не введена"
            else:
                gross_weight_str = f"{gross_weight:.0f}"
            
            # Стиль для данных в таблице
            data_style = ParagraphStyle(
                'DataStyle',
                parent=styles['Normal'],
                fontSize=7,
                fontName=font_name,
                textColor=colors.black,
            )
            
            # Используем Paragraph для правильной обработки кириллицы
            row = [
                Paragraph(str(position_num), data_style),
                Paragraph(f"{path_number}:{wagon_position}", data_style),
                Paragraph(wagon_number, data_style),
                Paragraph(wagon_type_name, data_style),
                Paragraph(f"{load_capacity:.1f}" if load_capacity else "", data_style),
                Paragraph(str(axle_count) if axle_count is not None else "", data_style),
                Paragraph(f"{net_weight:.0f}" if net_weight else "", data_style),
                Paragraph(f"{wagon_weight:.0f}" if wagon_weight else "", data_style),
                Paragraph(gross_weight_str, data_style),
                Paragraph(conductors_name, data_style),
                Paragraph(f"{body_volume:.1f}" if body_volume else "", data_style),
                Paragraph(f"{fill_height:.0f}" if fill_height else "", data_style),
                Paragraph(cistern_type_name, data_style),
            ]
            table_data.append(row)
        
        # Создаем таблицу с правильными размерами колонок
        col_widths = [
            15*mm,  # № п/п
            25*mm,  # № по расположению
            25*mm,  # № вагона
            30*mm,  # Тип вагона
            25*mm,  # Грузоподъёмность
            20*mm,  # Количество осей
            20*mm,  # Масса нетто
            20*mm,  # Масса вагона
            30*mm,  # Масса брутто
            25*mm,  # Проводники
            20*mm,  # Объём кузова
            20*mm,  # Высота налива
            25*mm,  # Тип цистерны
        ]
        
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Стиль таблицы (как в изображении - темно-серый заголовок, чередующиеся строки)
        table.setStyle(TableStyle([
            # Заголовок (темно-серый фон)
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#808080')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'CustomFont-Bold' if font_name == 'CustomFont' else 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            # Данные
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#E0E0E0')]),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            # Выравнивание для числовых колонок
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # № п/п
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),   # Грузоподъёмность
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Количество осей
            ('ALIGN', (6, 1), (8, -1), 'RIGHT'),   # Массы
            ('ALIGN', (10, 1), (11, -1), 'RIGHT'), # Объём и высота
        ]))
        
        elements.append(table)
        
        # Генерируем PDF
        doc.build(elements)
        
        return response
