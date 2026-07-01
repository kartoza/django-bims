# coding=utf-8
import os

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.db import connection
from django.http import FileResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models.checklist_version import ChecklistVersion, ChecklistVersionContributor
from bims.models.download_request import DownloadRequest
from bims.models.taxon_group import TaxonGroup
from bims.utils.filepath import ensure_within_dir, sanitize_path_component


def _auto_populate_contributors(version):
    """Create ChecklistVersionContributor rows from the taxon group's experts + contributors."""
    group = version.taxon_group
    seen_user_ids = set()
    rows = []
    order = 0
    for user in list(group.experts.all()) + list(group.contributors.all()):
        if user.pk in seen_user_ids:
            continue
        seen_user_ids.add(user.pk)
        rows.append(ChecklistVersionContributor(
            checklist_version=version,
            user=user,
            organisation=(getattr(user, 'organization', '') or '').strip(),
            order=order,
        ))
        order += 1
    if rows:
        ChecklistVersionContributor.objects.bulk_create(rows)


def _can_manage(user, version):
    return user.is_superuser or version.taxon_group.experts.filter(id=user.id).exists()


class ChecklistVersionContributorSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True, default='')
    last_name = serializers.CharField(source='user.last_name', read_only=True, default='')
    email = serializers.EmailField(source='user.email', read_only=True, default='')

    class Meta:
        model = ChecklistVersionContributor
        fields = ['id', 'user', 'first_name', 'last_name', 'email', 'organisation', 'note', 'order']
        read_only_fields = ['id', 'user', 'first_name', 'last_name', 'email']


class ChecklistVersionSerializer(serializers.ModelSerializer):
    taxon_group_name = serializers.CharField(
        source='taxon_group.name', read_only=True
    )
    published_by_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    contributors = serializers.SerializerMethodField()

    class Meta:
        model = ChecklistVersion
        fields = [
            'id',
            'version',
            'status',
            'taxon_group',
            'taxon_group_name',
            'doi',
            'dataset_key',
            'notes',
            'taxa_count',
            'additions_count',
            'updates_count',
            'deletions_count',
            'is_publishing',
            'created_at',
            'published_at',
            'published_by_name',
            'created_by_name',
            'previous_version',
            'license',
            'contributors',
        ]

    def get_published_by_name(self, obj):
        if obj.published_by:
            return obj.published_by.get_full_name() or obj.published_by.username
        return None

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def get_contributors(self, obj):
        return ChecklistVersionContributorSerializer(
            obj.version_contributors.select_related('user').order_by('order', 'id'),
            many=True,
        ).data


class ChecklistVersionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistVersion
        fields = [
            'taxon_group',
            'version',
            'doi',
            'notes',
            'previous_version',
            'license',
        ]
        validators = []  # suppress auto-generated UniqueTogetherValidator; custom check in validate()

    def validate(self, attrs):
        taxon_group = attrs.get('taxon_group')
        version = attrs.get('version', '').strip()
        if not version:
            raise serializers.ValidationError({'version': 'Version string is required.'})
        if ChecklistVersion.objects.filter(
            taxon_group=taxon_group, version=version
        ).exists():
            raise serializers.ValidationError(
                {'version': f'Version "{version}" already exists for this module.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        version = ChecklistVersion.objects.create(**validated_data)
        _auto_populate_contributors(version)
        return version


class ChecklistVersionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ChecklistVersionListView(APIView):
    """
    GET  — list published/draft checklist versions
    POST — create a new draft version (superusers only)
    """

    @swagger_auto_schema(
        operation_id='checklist_version_list',
        operation_summary='List checklist versions',
        operation_description=(
            'Returns a paginated list of ChecklistVersion records. '
            'Filter by taxon group using `?taxon_group=<id>`. '
            'Use `?status=draft` to include draft versions (superusers only).'
        ),
        manual_parameters=[
            openapi.Parameter(
                'taxon_group', openapi.IN_QUERY,
                description='Filter by TaxonGroup ID.',
                type=openapi.TYPE_INTEGER, required=False,
            ),
            openapi.Parameter(
                'status', openapi.IN_QUERY,
                description=(
                    '`published` (default), `draft`, or omit for all statuses '
                    '(superusers only — non-superusers always receive published only).'
                ),
                type=openapi.TYPE_STRING,
                enum=['published', 'draft'],
                required=False,
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description='Results per page (max 100).',
                type=openapi.TYPE_INTEGER, required=False,
            ),
        ],
        responses={200: ChecklistVersionSerializer(many=True)},
        tags=['Checklist'],
    )
    def get(self, request):
        status_param = request.query_params.get('status', '')
        taxon_group_id = request.query_params.get('taxon_group')
        can_manage_group = False
        if taxon_group_id and request.user.is_authenticated:
            can_manage_group = (
                request.user.is_superuser or
                TaxonGroup.objects.filter(
                    id=taxon_group_id,
                    experts=request.user
                ).exists()
            )

        qs = (
            ChecklistVersion.objects
            .select_related('taxon_group', 'published_by', 'created_by')
            .order_by('-created_at')
        )

        if request.user.is_superuser or can_manage_group:
            if status_param in (ChecklistVersion.STATUS_DRAFT, ChecklistVersion.STATUS_PUBLISHED):
                qs = qs.filter(status=status_param)
        else:
            qs = qs.filter(status=ChecklistVersion.STATUS_PUBLISHED)

        if taxon_group_id:
            qs = qs.filter(taxon_group_id=taxon_group_id)

        paginator = ChecklistVersionPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = ChecklistVersionSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_id='checklist_version_create',
        operation_summary='Create a draft checklist version',
        operation_description='Superusers only. Creates a new draft ChecklistVersion.',
        request_body=ChecklistVersionCreateSerializer,
        responses={
            201: ChecklistVersionSerializer(),
            400: openapi.Response(description='Validation error.'),
            403: openapi.Response(description='Superuser required.'),
        },
        tags=['Checklist'],
    )
    def post(self, request):
        if not request.user.is_superuser:
            return Response({'detail': 'Superuser access required.'}, status=403)

        serializer = ChecklistVersionCreateSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            obj = serializer.save()
            return Response(
                ChecklistVersionSerializer(obj, context={'request': request}).data,
                status=201,
            )
        return Response(serializer.errors, status=400)


class ChecklistVersionDetailView(APIView):
    """
    GET — retrieve a single checklist version by UUID.
    """

    @swagger_auto_schema(
        operation_id='checklist_version_detail',
        operation_summary='Retrieve a checklist version',
        responses={
            200: ChecklistVersionSerializer(),
            404: openapi.Response(description='Not found.'),
        },
        tags=['Checklist'],
    )
    def get(self, request, pk):
        try:
            obj = (
                ChecklistVersion.objects
                .select_related('taxon_group', 'published_by', 'previous_version')
                .get(pk=pk)
            )
        except ChecklistVersion.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        serializer = ChecklistVersionSerializer(obj, context={'request': request})
        return Response(serializer.data)


class ChecklistVersionPublishView(APIView):
    """
    POST /api/checklist-version/<uuid>/publish/
    Publish a draft ChecklistVersion (superusers only).
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='checklist_version_publish',
        operation_summary='Publish a draft checklist version',
        operation_description=(
            'Superusers only. Transitions a draft ChecklistVersion to published status, '
            'creates all ChecklistSnapshot rows, and stamps Taxonomy version UUIDs.'
        ),
        responses={
            200: ChecklistVersionSerializer(),
            400: openapi.Response(description='Already published.'),
            403: openapi.Response(description='Superuser required.'),
            404: openapi.Response(description='Not found.'),
        },
        tags=['Checklist'],
    )
    def post(self, request, pk):
        try:
            obj = ChecklistVersion.objects.select_related('taxon_group').get(pk=pk)
        except ChecklistVersion.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        can_publish = (
            request.user.is_superuser or
            obj.taxon_group.experts.filter(id=request.user.id).exists()
        )
        if not can_publish:
            return Response(
                {'detail': 'Admin or taxon group expert access required.'},
                status=403
            )

        if obj.status == ChecklistVersion.STATUS_PUBLISHED:
            return Response({'detail': 'Already published.'}, status=400)

        if obj.is_publishing:
            return Response({'detail': 'Already publishing.'}, status=400)

        # Mark as publishing immediately so the UI reflects it right away,
        # then hand off to Celery so the endpoint returns without blocking.
        obj.is_publishing = True
        obj.save(update_fields=['is_publishing'])

        from django.db import connection
        from bims.tasks.checklist import publish_versions_task
        publish_versions_task.delay(
            schema_name=connection.schema_name,
            version_ids=[str(obj.pk)],
            published_by_id=request.user.pk,
        )

        obj.refresh_from_db()
        return Response(
            ChecklistVersionSerializer(obj, context={'request': request}).data,
            status=202,
        )


class ChecklistVersionDraftDeleteView(APIView):
    """DELETE a draft checklist version immediately (synchronous)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            obj = ChecklistVersion.objects.select_related('taxon_group').get(pk=pk)
        except ChecklistVersion.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        if not _can_manage(request.user, obj):
            return Response(
                {'detail': 'Admin or taxon group expert access required.'},
                status=403,
            )
        if obj.status != ChecklistVersion.STATUS_DRAFT:
            return Response(
                {'detail': 'Only draft checklist versions can be deleted this way.'},
                status=400,
            )
        obj.delete()
        return Response({'message': 'Draft deleted.'}, status=200)


class ChecklistVersionDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            obj = ChecklistVersion.objects.select_related('taxon_group').get(pk=pk)
        except ChecklistVersion.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        can_delete = (
            request.user.is_superuser or
            obj.taxon_group.experts.filter(id=request.user.id).exists()
        )
        if not can_delete:
            return Response(
                {'detail': 'Admin or taxon group expert access required.'},
                status=403
            )

        if obj.status != ChecklistVersion.STATUS_PUBLISHED:
            return Response(
                {'detail': 'Only published checklist versions can be removed.'},
                status=400
            )

        from bims.tasks.checklist import delete_published_checklist_version_task
        delete_published_checklist_version_task.delay(
            str(connection.schema_name),
            str(obj.pk),
        )
        return Response({
            'message': 'Checklist removal queued.'
        }, status=202)


class ChecklistVersionExportView(APIView):
    """
    POST /api/checklist-version/<uuid>/export/
        Enqueue a ColDP ZIP export for a published ChecklistVersion.
        Returns {download_request_id, status_url}.

    GET /api/checklist-version/<uuid>/export/?download_request_id=<id>
        Stream the completed ZIP file.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            version = ChecklistVersion.objects.get(pk=pk)
        except ChecklistVersion.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        if version.status != ChecklistVersion.STATUS_PUBLISHED:
            return Response({'detail': 'Only published versions can be exported.'}, status=400)

        download_request_id = request.data.get('download_request_id')
        if download_request_id:
            try:
                dr = DownloadRequest.objects.get(
                    id=download_request_id,
                    requester=request.user,
                )
            except DownloadRequest.DoesNotExist:
                return Response({'detail': 'Download request not found.'}, status=404)

            if dr.request_file:
                return Response({
                    'download_request_id': dr.id,
                    'status_url': f'/api/download-request/{dr.id}/progress/',
                    'download_url': f'/api/download-request/{dr.id}/file/',
                })

            if dr.processing and dr.progress:
                return Response({
                    'download_request_id': dr.id,
                    'status_url': f'/api/download-request/{dr.id}/progress/',
                    'download_url': f'/api/download-request/{dr.id}/file/',
                }, status=202)

            dr.processing = True
            dr.resource_type = DownloadRequest.ZIP
            dr.resource_name = f'Checklist ColDP ZIP {version.pk}'
            dr.request_category = f'{version.taxon_group.name} {version.version}'
            dr.approved = True
            dr.save(update_fields=[
                'processing',
                'resource_type',
                'resource_name',
                'request_category',
                'approved',
            ])
        else:
            dr = DownloadRequest.objects.create(
                requester=request.user,
                resource_type=DownloadRequest.ZIP,
                resource_name=f'Checklist ColDP ZIP {version.pk}',
                request_category=f'{version.taxon_group.name} {version.version}',
                approved=True,
                processing=True,
            )

        from bims.tasks.coldp_export import export_coldp_zip
        export_coldp_zip.delay(dr.id, str(version.pk))

        return Response({
            'download_request_id': dr.id,
            'status_url': f'/api/download-request/{dr.id}/progress/',
            'download_url': f'/api/download-request/{dr.id}/file/',
        }, status=202)

    def get(self, request, pk):
        """Stream the ZIP once export is complete."""
        dr_id = request.query_params.get('download_request_id')
        if not dr_id:
            return Response({'detail': 'download_request_id is required.'}, status=400)

        try:
            dr = DownloadRequest.objects.get(id=dr_id, requester=request.user)
        except DownloadRequest.DoesNotExist:
            return Response({'detail': 'Download request not found.'}, status=404)

        if dr.processing:
            return Response({'detail': 'Export still in progress.'}, status=202)

        if dr.request_file:
            return FileResponse(
                dr.request_file.open('rb'),
                content_type='application/zip',
                as_attachment=True,
                filename=dr.request_category or os.path.basename(dr.request_file.name),
            )

        file_path = dr.download_path
        if not file_path or not os.path.exists(file_path):
            return Response({'detail': 'Export file not found.'}, status=404)

        try:
            safe_file_path = ensure_within_dir(file_path, settings.MEDIA_ROOT)
        except SuspiciousFileOperation:
            return Response({'detail': 'Export file not found.'}, status=404)

        filename = sanitize_path_component(
            dr.request_category or os.path.basename(safe_file_path),
            'checklist',
        )
        response = FileResponse(
            open(safe_file_path, 'rb'),
            content_type='application/zip',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ChecklistVersionContributorListView(APIView):
    """
    GET  /api/checklist-version/<uuid>/contributors/  — list contributors
    POST /api/checklist-version/<uuid>/contributors/  — add org-only contributor
    """
    permission_classes = [IsAuthenticated]

    def _get_version(self, pk):
        try:
            return ChecklistVersion.objects.select_related('taxon_group').get(pk=pk)
        except ChecklistVersion.DoesNotExist:
            return None

    def get(self, request, pk):
        version = self._get_version(pk)
        if not version:
            return Response({'detail': 'Not found.'}, status=404)
        qs = version.version_contributors.select_related('user')
        return Response(ChecklistVersionContributorSerializer(qs, many=True).data)

    def post(self, request, pk):
        version = self._get_version(pk)
        if not version:
            return Response({'detail': 'Not found.'}, status=404)
        if not _can_manage(request.user, version):
            return Response({'detail': 'Admin or expert access required.'}, status=403)
        organisation = request.data.get('organisation', '').strip()
        if not organisation:
            return Response({'detail': 'organisation is required for org-only entries.'}, status=400)
        order = version.version_contributors.count()
        contributor = ChecklistVersionContributor.objects.create(
            checklist_version=version,
            user=None,
            organisation=organisation,
            note=request.data.get('note', '').strip(),
            order=order,
        )
        return Response(ChecklistVersionContributorSerializer(contributor).data, status=201)


class ChecklistVersionContributorDetailView(APIView):
    """
    PATCH  /api/checklist-version/<uuid>/contributors/<id>/  — update organisation/note
    DELETE /api/checklist-version/<uuid>/contributors/<id>/  — remove
    """
    permission_classes = [IsAuthenticated]

    def _get_objects(self, pk, contributor_id):
        try:
            version = ChecklistVersion.objects.select_related('taxon_group').get(pk=pk)
        except ChecklistVersion.DoesNotExist:
            return None, None
        try:
            contributor = version.version_contributors.get(pk=contributor_id)
        except ChecklistVersionContributor.DoesNotExist:
            return version, None
        return version, contributor

    def patch(self, request, pk, contributor_id):
        version, contributor = self._get_objects(pk, contributor_id)
        if not version:
            return Response({'detail': 'Not found.'}, status=404)
        if not contributor:
            return Response({'detail': 'Contributor not found.'}, status=404)
        if not _can_manage(request.user, version):
            return Response({'detail': 'Admin or expert access required.'}, status=403)
        if 'organisation' in request.data:
            contributor.organisation = request.data['organisation']
        if 'note' in request.data:
            contributor.note = request.data['note']
        contributor.save(update_fields=['organisation', 'note'])
        return Response(ChecklistVersionContributorSerializer(contributor).data)

    def delete(self, request, pk, contributor_id):
        version, contributor = self._get_objects(pk, contributor_id)
        if not version:
            return Response({'detail': 'Not found.'}, status=404)
        if not contributor:
            return Response({'detail': 'Contributor not found.'}, status=404)
        if not _can_manage(request.user, version):
            return Response({'detail': 'Admin or expert access required.'}, status=403)
        contributor.delete()
        return Response(status=204)


class TaxonGroupMembersView(APIView):
    """
    GET /api/checklist-version/group-members/?taxon_group=<id>
    Returns the experts + contributors of a TaxonGroup as a contributor preview,
    used to pre-populate the "Add Version" modal before the version is created.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        group_id = request.query_params.get('taxon_group')
        if not group_id:
            return Response({'detail': 'taxon_group is required.'}, status=400)
        try:
            group = TaxonGroup.objects.get(pk=group_id)
        except TaxonGroup.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        seen = set()
        members = []
        for user in list(group.experts.all()) + list(group.contributors.all()):
            if user.pk in seen:
                continue
            seen.add(user.pk)
            members.append({
                'user': user.pk,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'organisation': (getattr(user, 'organization', '') or '').strip(),
                'note': '',
            })
        return Response(members)
