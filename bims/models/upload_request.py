# coding=utf-8
import os
import uuid
from django.db import models
from django.conf import settings

def upload_path(instance, filename):
    base, ext = os.path.splitext(filename)
    return f"uploads/{instance.created_at:%Y/%m/%d}/{uuid.uuid4().hex}{ext.lower()}"

class UploadRequest(models.Model):
    OCCURRENCE = 'occurrence'
    SPATIAL = 'spatial'
    SPECIES_CHECKLIST_OR_TAXONOMIC_RESOURCE = 'species-checklist'
    
    TYPE_CHOICES = (
        (OCCURRENCE, 'Occurrence Data'),
        (SPATIAL, 'Spatial Layer'),
        (SPECIES_CHECKLIST_OR_TAXONOMIC_RESOURCE, 'Species Checklist or Taxonomic Resource'),
    )

    STATUS_SUBMITTED = 'submitted'
    STATUS_TICKETED = 'ticketed'
    STATUS_ERROR = 'error'
    STATUS_CHOICES = (
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_TICKETED, 'Ticket Created'),
        (STATUS_ERROR, 'Error'),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='uploads'
    )

    title = models.CharField(max_length=255, blank=True, default='')
    name = models.CharField(max_length=255)
    email = models.EmailField()
    upload_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    upload_file = models.FileField(upload_to=upload_path)
    notes = models.TextField(blank=True)
    source = models.CharField(max_length=255, blank=True)
    client_ip = models.GenericIPAddressField(null=True, blank=True)

    github_issue_number = models.IntegerField(null=True, blank=True)
    github_issue_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.get_upload_type_display()} by {self.name} on {self.created_at:%Y-%m-%d}"

    @property
    def file_name(self):
        return os.path.basename(self.upload_file.name)
