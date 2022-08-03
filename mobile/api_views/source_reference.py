from bims.views.source_reference import SourceReferenceAPIView


class SourceReferenceMobileList(SourceReferenceAPIView):
    def get_queryset(self):
        qs = super(SourceReferenceMobileList, self).get_queryset()
        qs = qs.filter(mobile=True)
        return qs
