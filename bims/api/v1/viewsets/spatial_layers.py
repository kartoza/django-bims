# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
API ViewSets for spatial layer management.

Provides endpoints for uploading, publishing, and managing spatial layers
including cloud native GIS layers, visualization layers, and context filters.

Made with love by Kartoza | https://kartoza.com
"""
import os
import uuid
import tempfile
import json

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from cloud_native_gis.models import Layer, LayerType, LayerUpload, UploadStatus

from bims.models.non_biodiversity_layer import NonBiodiversityLayer
from bims.models.location_context_group import LocationContextGroup


# Serializers
class CloudNativeLayerSerializer(serializers.ModelSerializer):
    """Serializer for cloud native GIS layers."""
    attributes = serializers.SerializerMethodField()
    maputnik_url = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_attributes(self, obj: Layer):
        return obj.attribute_names if hasattr(obj, 'attribute_names') else []

    def get_maputnik_url(self, obj: Layer):
        request = self.context.get('request')
        if request and hasattr(obj, 'maputnik_url'):
            return obj.maputnik_url(request)
        return None

    def get_status(self, obj: Layer):
        """Return layer status based on is_ready flag."""
        return 'ready' if obj.is_ready else 'processing'

    class Meta:
        model = Layer
        fields = [
            'id', 'unique_id', 'name', 'abstract',
            'attributes', 'maputnik_url', 'is_ready', 'status'
        ]


class LayerUploadSessionSerializer(serializers.ModelSerializer):
    """Serializer for layer upload sessions."""
    layer = CloudNativeLayerSerializer(read_only=True)
    maputnik_url = serializers.SerializerMethodField()
    created_by = serializers.StringRelatedField()
    error_message = serializers.CharField(source='note', read_only=True)
    status_display = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    has_style = serializers.SerializerMethodField()

    def get_status(self, obj: LayerUpload):
        """Return normalized lowercase status for frontend."""
        status_map = {
            UploadStatus.START: 'pending',
            UploadStatus.RUNNING: 'processing',
            UploadStatus.SUCCESS: 'success',
            UploadStatus.FAILED: 'failed',
        }
        return status_map.get(obj.status, 'pending')

    def get_maputnik_url(self, obj: LayerUpload):
        request = self.context.get('request')
        if obj.status == UploadStatus.SUCCESS and obj.layer and request:
            return obj.layer.maputnik_url(request)
        return None

    def get_has_style(self, obj: LayerUpload):
        """Check if the layer has a style defined."""
        if obj.layer:
            # Check if layer has a default style or any styles
            return obj.layer.default_style is not None or obj.layer.styles.exists()
        return False

    def get_status_display(self, obj: LayerUpload):
        """Return human-readable status message."""
        status_messages = {
            UploadStatus.START: 'Queued for processing...',
            UploadStatus.RUNNING: 'Converting to vector tiles...',
            UploadStatus.SUCCESS: 'Ready for styling',
            UploadStatus.FAILED: 'Processing failed',
        }
        return status_messages.get(obj.status, 'Unknown status')

    class Meta:
        model = LayerUpload
        fields = [
            'id', 'layer', 'status', 'progress', 'created_at',
            'created_by', 'maputnik_url', 'error_message', 'status_display',
            'has_style'
        ]


class VisualizationLayerSerializer(serializers.ModelSerializer):
    """Serializer for visualization layers (NonBiodiversityLayer)."""
    native_layer = CloudNativeLayerSerializer(read_only=True)
    visible = serializers.BooleanField(source='default_visibility', read_only=True)

    class Meta:
        model = NonBiodiversityLayer
        fields = [
            'id', 'name', 'wms_url', 'wms_layer_name',
            'native_layer', 'order', 'default_visibility', 'visible'
        ]
        read_only_fields = ['order']


class ContextLayerGroupSerializer(serializers.ModelSerializer):
    """Serializer for context layer groups."""
    site_count = serializers.SerializerMethodField()
    native_layer = serializers.SerializerMethodField()

    def get_site_count(self, obj: LocationContextGroup):
        """Count sites that have context data for this group."""
        from bims.models.location_context import LocationContext
        return LocationContext.objects.filter(
            group=obj
        ).exclude(
            value=''
        ).values('site').distinct().count()

    def get_native_layer(self, obj: LocationContextGroup):
        """Get native layer info if key is a UUID."""
        if obj.key and ':' in obj.key:
            uuid_part = obj.key.split(':')[0]
            try:
                layer = Layer.objects.get(unique_id=uuid_part)
                return CloudNativeLayerSerializer(
                    layer,
                    context=self.context
                ).data
            except (Layer.DoesNotExist, ValueError):
                pass
        return None

    class Meta:
        model = LocationContextGroup
        fields = [
            'id', 'name', 'key', 'layer_identifier',
            'geocontext_group_key', 'native_layer', 'site_count'
        ]


# ViewSets
class CloudNativeLayerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing available cloud native GIS layers.

    These are vector tile layers that have been uploaded and processed.
    """
    serializer_class = CloudNativeLayerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Include all vector tile layers, not just ready ones
        # The frontend will show status for layers still processing
        return Layer.objects.filter(
            layer_type=LayerType.VECTOR_TILE
        ).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data})


class SpatialLayerUploadViewSet(viewsets.ViewSet):
    """
    ViewSet for uploading spatial layers (shapefiles to vector tiles).

    Supports uploading shapefile components which are then processed
    into PMTiles format for vector tile serving.
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def list(self, request):
        """List all upload sessions."""
        sessions = LayerUpload.objects.all().order_by('-created_at')
        serializer = LayerUploadSessionSerializer(
            sessions,
            many=True,
            context={'request': request}
        )
        return Response({'data': serializer.data})

    def create(self, request):
        """Upload shapefile and create processing job."""
        name = request.data.get('name')
        files = request.FILES.getlist('files')

        if not name:
            return Response(
                {'message': 'Layer name is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not files:
            return Response(
                {'message': 'At least one file is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for required shapefile components
        extensions = {f.name.split('.')[-1].lower() for f in files}
        required = {'shp', 'shx', 'dbf'}
        if not required.issubset(extensions):
            return Response(
                {
                    'message': 'Missing required shapefile components. '
                               'Please include .shp, .shx, and .dbf files.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Create the layer
            unique_id = uuid.uuid4()
            layer = Layer.objects.create(
                unique_id=unique_id,
                layer_type=LayerType.VECTOR_TILE,
                created_by=request.user,
                name=name
            )

            # Create upload session
            upload_session = LayerUpload(
                created_by=request.user,
                layer=layer
            )
            upload_session.emptying_folder()

            # Save uploaded files
            storage = FileSystemStorage(location=upload_session.folder)
            for f in files:
                storage.save(f.name, f)

            upload_session.save()

            serializer = LayerUploadSessionSerializer(
                upload_session,
                context={'request': request}
            )

            return Response(
                {
                    'message': 'Upload started successfully.',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'message': f'Upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='upload-sessions')
    def upload_sessions(self, request):
        """Get upload sessions (alias for list)."""
        return self.list(request)

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        """Upload endpoint (alias for create)."""
        return self.create(request)

    @action(detail=False, methods=['post'], url_path='upload/init',
            parser_classes=[JSONParser])
    def init_chunked_upload(self, request):
        """Initialize a chunked upload session."""
        name = request.data.get('name')
        upload_id = request.data.get('upload_id')
        total_size = request.data.get('total_size')
        file_count = request.data.get('file_count')
        file_names = request.data.get('file_names', [])

        if not all([name, upload_id, total_size, file_count]):
            return Response(
                {'message': 'Missing required fields.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create a temporary directory for this upload
        upload_dir = os.path.join(
            tempfile.gettempdir(),
            'bims_chunked_uploads',
            upload_id
        )
        os.makedirs(upload_dir, exist_ok=True)

        # Store session info in cache
        session_data = {
            'name': name,
            'upload_id': upload_id,
            'total_size': total_size,
            'file_count': file_count,
            'file_names': file_names,
            'upload_dir': upload_dir,
            'user_id': request.user.id,
            'chunks_received': {},
        }
        cache.set(f'chunked_upload_{upload_id}', json.dumps(session_data), timeout=3600)

        return Response({
            'session_id': upload_id,
            'message': 'Chunked upload initialized.',
        })

    @action(detail=False, methods=['post'], url_path='upload/chunk')
    def upload_chunk(self, request):
        """Upload a single chunk of a file."""
        session_id = request.data.get('session_id')
        file_name = request.data.get('file_name')
        chunk_index = int(request.data.get('chunk_index', 0))
        total_chunks = int(request.data.get('total_chunks', 1))
        chunk = request.FILES.get('chunk')

        if not all([session_id, file_name, chunk]):
            return Response(
                {'message': 'Missing required fields.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get session data from cache
        session_json = cache.get(f'chunked_upload_{session_id}')
        if not session_json:
            return Response(
                {'message': 'Upload session not found or expired.'},
                status=status.HTTP_404_NOT_FOUND
            )

        session_data = json.loads(session_json)
        upload_dir = session_data['upload_dir']

        # Create directory for this file's chunks
        file_chunk_dir = os.path.join(upload_dir, file_name)
        os.makedirs(file_chunk_dir, exist_ok=True)

        # Save the chunk
        chunk_path = os.path.join(file_chunk_dir, f'chunk_{chunk_index:05d}')
        with open(chunk_path, 'wb') as f:
            for data in chunk.chunks():
                f.write(data)

        # Track received chunks
        if file_name not in session_data['chunks_received']:
            session_data['chunks_received'][file_name] = {
                'total': total_chunks,
                'received': []
            }
        session_data['chunks_received'][file_name]['received'].append(chunk_index)

        # Update cache
        cache.set(f'chunked_upload_{session_id}', json.dumps(session_data), timeout=3600)

        return Response({
            'message': f'Chunk {chunk_index + 1}/{total_chunks} received.',
            'chunk_index': chunk_index,
        })

    @action(detail=False, methods=['post'], url_path='upload/finalize',
            parser_classes=[JSONParser])
    def finalize_chunked_upload(self, request):
        """Finalize a chunked upload and start processing."""
        session_id = request.data.get('session_id')

        if not session_id:
            return Response(
                {'message': 'Session ID required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get session data from cache
        session_json = cache.get(f'chunked_upload_{session_id}')
        if not session_json:
            return Response(
                {'message': 'Upload session not found or expired.'},
                status=status.HTTP_404_NOT_FOUND
            )

        session_data = json.loads(session_json)
        upload_dir = session_data['upload_dir']
        name = session_data['name']

        try:
            # Reassemble files from chunks
            assembled_files = []
            for file_name in session_data['file_names']:
                file_chunk_dir = os.path.join(upload_dir, file_name)
                if not os.path.exists(file_chunk_dir):
                    continue

                # Get all chunks and sort them
                chunks = sorted([
                    f for f in os.listdir(file_chunk_dir)
                    if f.startswith('chunk_')
                ])

                # Reassemble the file
                assembled_path = os.path.join(upload_dir, file_name)
                with open(assembled_path, 'wb') as output:
                    for chunk_name in chunks:
                        chunk_path = os.path.join(file_chunk_dir, chunk_name)
                        with open(chunk_path, 'rb') as chunk_file:
                            output.write(chunk_file.read())

                assembled_files.append(assembled_path)

                # Clean up chunk directory
                import shutil
                shutil.rmtree(file_chunk_dir)

            # Check for required shapefile components
            extensions = {f.split('.')[-1].lower() for f in assembled_files}
            required = {'shp', 'shx', 'dbf'}
            if not required.issubset(extensions):
                return Response(
                    {
                        'message': 'Missing required shapefile components. '
                                   'Please include .shp, .shx, and .dbf files.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create the layer
            unique_id = uuid.uuid4()
            layer = Layer.objects.create(
                unique_id=unique_id,
                layer_type=LayerType.VECTOR_TILE,
                created_by=request.user,
                name=name
            )

            # Create upload session
            upload_session = LayerUpload(
                created_by=request.user,
                layer=layer
            )
            upload_session.emptying_folder()

            # Copy assembled files to the upload session folder
            storage = FileSystemStorage(location=upload_session.folder)
            for file_path in assembled_files:
                file_name = os.path.basename(file_path)
                with open(file_path, 'rb') as f:
                    storage.save(file_name, ContentFile(f.read()))

            upload_session.save()

            # Clean up temp directory
            import shutil
            shutil.rmtree(upload_dir, ignore_errors=True)

            # Clear cache
            cache.delete(f'chunked_upload_{session_id}')

            serializer = LayerUploadSessionSerializer(
                upload_session,
                context={'request': request}
            )

            return Response({
                'message': 'Upload completed successfully.',
                'data': serializer.data
            })

        except Exception as e:
            # Clean up on error
            import shutil
            shutil.rmtree(upload_dir, ignore_errors=True)
            cache.delete(f'chunked_upload_{session_id}')

            return Response(
                {'message': f'Upload finalization failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, pk=None):
        """Delete an upload session and its associated layer if processing failed."""
        try:
            session = LayerUpload.objects.get(pk=pk)
        except LayerUpload.DoesNotExist:
            return Response(
                {'message': 'Upload session not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only allow deleting failed or completed sessions, not ones still processing
        if session.status in [UploadStatus.START, UploadStatus.RUNNING]:
            return Response(
                {'message': 'Cannot delete a session that is still processing.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete the associated layer if it exists and has no published visualization
        layer = session.layer
        if layer:
            # Check if this layer is published as a visualization layer
            has_viz_layer = NonBiodiversityLayer.objects.filter(
                native_layer=layer
            ).exists()
            if has_viz_layer:
                return Response(
                    {
                        'message': 'Cannot delete: This layer is published as '
                                   'a visualization layer. Unpublish it first.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Delete the layer (will cascade to upload session)
            layer.delete()
        else:
            # Just delete the session
            session.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['delete'], url_path='clear-failed')
    def clear_failed(self, request):
        """Delete all failed upload sessions."""
        failed_sessions = LayerUpload.objects.filter(status=UploadStatus.FAILED)

        # Filter out any that have published visualization layers
        deletable = []
        for session in failed_sessions:
            if session.layer:
                has_viz = NonBiodiversityLayer.objects.filter(
                    native_layer=session.layer
                ).exists()
                if not has_viz:
                    deletable.append(session)
            else:
                deletable.append(session)

        count = len(deletable)
        for session in deletable:
            if session.layer:
                session.layer.delete()
            else:
                session.delete()

        return Response({
            'message': f'Deleted {count} failed upload session(s).',
            'count': count
        })


class VisualizationLayerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing visualization layers on the map.

    These layers appear in the map legend and can be toggled by users.
    """
    serializer_class = VisualizationLayerSerializer
    permission_classes = [IsAdminUser]
    queryset = NonBiodiversityLayer.objects.all().order_by('order')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data})

    def create(self, request, *args, **kwargs):
        """Publish a cloud native layer as a visualization layer."""
        native_layer_uuid = request.data.get('native_layer_uuid')
        name = request.data.get('name')

        if not native_layer_uuid or not name:
            return Response(
                {'message': 'native_layer_uuid and name are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            native_layer = Layer.objects.get(unique_id=native_layer_uuid)
        except Layer.DoesNotExist:
            return Response(
                {'message': 'Layer not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if already published
        if NonBiodiversityLayer.objects.filter(native_layer=native_layer).exists():
            return Response(
                {'message': 'This layer is already published.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create visualization layer with the layer's default style if available
        viz_layer = NonBiodiversityLayer.objects.create(
            name=name,
            native_layer=native_layer,
            native_layer_style=native_layer.default_style,
            wms_layer_name=str(native_layer.unique_id),
            default_visibility=False
        )

        serializer = self.get_serializer(viz_layer)
        return Response(
            {'data': serializer.data},
            status=status.HTTP_201_CREATED
        )

    def partial_update(self, request, *args, **kwargs):
        """Update layer properties (name, visibility, etc.)."""
        instance = self.get_object()

        if 'name' in request.data:
            instance.name = request.data['name']
        if 'visible' in request.data:
            instance.default_visibility = request.data['visible']

        instance.save()

        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data})

    @action(detail=True, methods=['post'], url_path='move-up')
    def move_up(self, request, pk=None):
        """Move layer up in the order."""
        instance = self.get_object()
        instance.up()
        return Response({'status': 'moved up'})

    @action(detail=True, methods=['post'], url_path='move-down')
    def move_down(self, request, pk=None):
        """Move layer down in the order."""
        instance = self.get_object()
        instance.down()
        return Response({'status': 'moved down'})


class ContextLayerGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing context layer groups.

    Context layers are used for geocontext lookups on location sites.
    They extract spatial attributes to enrich site data.
    """
    serializer_class = ContextLayerGroupSerializer
    permission_classes = [IsAdminUser]
    queryset = LocationContextGroup.objects.all().order_by('order')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data})

    def create(self, request, *args, **kwargs):
        """Add a new context layer group."""
        name = request.data.get('name')
        key = request.data.get('key')
        layer_identifier = request.data.get('layer_identifier')

        if not name or not key:
            return Response(
                {'message': 'name and key are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already exists
        if LocationContextGroup.objects.filter(key=key).exists():
            return Response(
                {'message': 'A context group with this key already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        group = LocationContextGroup.objects.create(
            name=name,
            key=key,
            layer_identifier=layer_identifier or ''
        )

        serializer = self.get_serializer(group)
        return Response(
            {'data': serializer.data},
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a context layer group."""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
