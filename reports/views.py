import csv
import io

from django.db.models import Count
from django.http import HttpResponse
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from openpyxl import Workbook

from operations.models import Operation
from users.permissions import IsObserverOrAbove


class StatsView(APIView):
    permission_classes = [IsObserverOrAbove]

    def get(self, request):
        total_ops = Operation.objects.count()
        by_action = Operation.objects.values('action_type').annotate(count=Count('id')).order_by('-count')
        data = {
            'total_operations': total_ops,
            'by_action': list(by_action),
        }
        return Response(data)


class ReportView(APIView):
    permission_classes = [IsObserverOrAbove]

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
            rows.append({
                'id': op.id,
                'equipment_id': str(op.equipment_id),
                'equipment_name': op.equipment.name,
                'action_type': op.action_type,
                'user': op.user.username,
                'target_user': op.target_user.username if op.target_user else '',
                'timestamp': op.timestamp.isoformat(),
                'notes': op.notes,
            })
        export_format = request.query_params.get('format')
        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=rows[0].keys() if rows else [])
            if rows:
                writer.writeheader()
                writer.writerows(rows)
            response = HttpResponse(output.getvalue(), content_type='text/csv')
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
