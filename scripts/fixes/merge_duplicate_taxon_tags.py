from django.db import transaction
from django.db.models import Count
from django.utils.text import slugify
from django_tenants.utils import schema_context

from bims.models.taxonomy import TaxonTag, CustomTaggedTaxonomy
from bims.models.taxonomy_update_proposal import CustomTaggedUpdateTaxonomy


def _reassign_and_delete(duplicate, survivor):
    for through in (CustomTaggedTaxonomy, CustomTaggedUpdateTaxonomy):
        fk = through._meta.get_field('content_object').attname
        for row in through.objects.filter(tag_id=duplicate.id):
            if through.objects.filter(**{fk: getattr(row, fk)}, tag_id=survivor.id).exists():
                row.delete()
            else:
                row.tag = survivor
                row.save(update_fields=['tag'])
    duplicate.delete()


with schema_context('fada'):
    # Step 1: strip whitespace from all TaxonTag names.
    dirty_tags = [t for t in TaxonTag.objects.all() if t.name != t.name.strip()]
    print(f'Tags with surrounding whitespace: {len(dirty_tags)}')

    with transaction.atomic():
        for tag in dirty_tags:
            clean_name = tag.name.strip()
            existing = TaxonTag.objects.filter(name=clean_name, doubtful=tag.doubtful).exclude(pk=tag.pk).order_by('id').first()
            if existing:
                print(f'  Merging "{tag.name!r}" (id={tag.id}) -> existing "{existing.name}" (id={existing.id})')
                _reassign_and_delete(tag, existing)
            else:
                new_slug = slugify(clean_name, allow_unicode=True)
                if TaxonTag.objects.filter(slug=new_slug).exclude(pk=tag.pk).exists():
                    i = 1
                    while TaxonTag.objects.filter(slug=f'{new_slug}_{i}').exclude(pk=tag.pk).exists():
                        i += 1
                    new_slug = f'{new_slug}_{i}'
                print(f'  Stripping "{tag.name!r}" -> "{clean_name}" (id={tag.id})')
                tag.name = clean_name
                tag.slug = new_slug
                tag.save(update_fields=['name', 'slug'])

    # Step 2: merge any remaining (name, doubtful) duplicates.
    groups = (
        TaxonTag.objects
        .values('name', 'doubtful')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
    )
    print(f'Remaining duplicate (name, doubtful) group(s): {groups.count()}')

    for group in groups:
        tags = list(TaxonTag.objects.filter(name=group['name'], doubtful=group['doubtful']).order_by('id'))
        survivor = tags[0]
        duplicates = tags[1:]
        print(f'  "{survivor.name}" doubtful={survivor.doubtful}: keeping id={survivor.id}, merging {[t.id for t in duplicates]}')
        with transaction.atomic():
            for dup in duplicates:
                _reassign_and_delete(dup, survivor)

    print('Done.')
