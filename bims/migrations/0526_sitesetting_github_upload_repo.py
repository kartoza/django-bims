from django.db import migrations, models


def copy_feedback_repo_to_upload_repo(apps, schema_editor):
    SiteSetting = apps.get_model('bims', 'SiteSetting')
    for obj in SiteSetting.objects.all():
        if obj.github_feedback_repo and not obj.github_upload_repo:
            obj.github_upload_repo = obj.github_feedback_repo
            obj.save(update_fields=['github_upload_repo'])


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0525_taxongroup_is_readonly_taxongroup_upstream_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='github_upload_repo',
            field=models.CharField(
                blank=True,
                default='',
                help_text=(
                    'GitHub repository where upload issues are created, '
                    'in "owner/repo" format (e.g. "my-org/upload-tracker"). '
                    'The GitHub App must be installed on this repository.'
                ),
                max_length=200,
            ),
        ),
        migrations.RunPython(
            copy_feedback_repo_to_upload_repo,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
