import csv
import io

from django.db.models import Count
from django.http import HttpResponse
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from openpyxl import Workbook

from operations.models import Operation
from users.permissions import IsStorekeeperOrAdmin


class StatsView(APIView):
    permission_classes = [IsStorekeeperOrAdmin]

    def get(self, request):
        total_ops = Operation.objects.count()
        by_action = Operation.objects.values('action_type').annotate(count=Count('id')).order_by('-count')
        data = {
            'total_operations': total_ops,
            'by_action': list(by_action),
        }
        return Response(data)


class ReportView(APIView):
    permission_classes = [IsStorekeeperOrAdmin]

    def get(self, request):
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        qs = Operation.objects.select_related('equipment', 'user', 'target_user').all()
        if start:
            qs = qs.filter(timestamp__gte=start)
        if end:
            qs = qs.filter(timestamp__lte=end)
        rows = []
        for op in qs:
            action_label = op.get_action_type_display()
            rows.append({
                'ID': op.id,
                'ID оборудования': str(op.equipment_id),
                'Наименование оборудования': op.equipment.name,
                'Тип операции': action_label,
                'Пользователь': op.user.username,
                'Получатель': op.target_user.username if op.target_user else '',
                'Дата и время': op.timestamp.isoformat(),
                'Комментарий': op.notes,
            })
        export_format = request.query_params.get('format')
        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=rows[0].keys() if rows else [])
            if rows:
                writer.writeheader()
                writer.writerows(rows)
            csv_text = '\ufeff' + output.getvalue()
            response = HttpResponse(csv_text, content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="report.csv"'
            return response
        if export_format == 'xlsx':
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = 'Report'
            if rows:
                sheet.append(list(rows[0].keys()))
                for row in rows:
                    sheet.append(list(row.values()))
            output = io.BytesIO()
            workbook.save(output)
            output.seek(0)
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = 'attachment; filename="report.xlsx"'
            return response
        return Response(rows)
