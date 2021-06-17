from django.views.generic import ListView
from bims.models.survey import Survey


# class SurveyTable(tables.Table):
#
#     delete = tables.TemplateColumn(
#         '<a href="/site-visit/update/{{record.id}}/" class="btn btn-primary">'
#             '<i class="fa fa-pencil"></i>'
#         '</a>'
#         '<a href="#" class="btn btn-danger del" data-id="{{ record.id }}">'
#             '<i class="fa fa-trash-o"></i>'
#         '</a>'
#         '<a href="#" class="btn btn-success send" data-id="{{ record.id}}">'
#             '<i class="fa fa-send"></i>'
#         '</a>'
#     )
#
#     class Meta:
#         model = Survey
#         template_name = 'django_tables2/bootstrap4.html'
#         fields = ('id', 'site', 'date')
#
#
# class NonValidatedSurveyListView(tables.SingleTableView):
#     model = Survey
#     table_class = SurveyTable
#     template_name = 'survey_list.html'
#
#     def get_table_data(self):
#         return Survey.objects.filter(
#             owner=self.request.user
#         )
