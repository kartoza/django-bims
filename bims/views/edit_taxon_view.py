from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import UpdateView

from bims.api_views.taxon_update import is_expert, create_taxon_proposal, update_taxon_proposal
from bims.models import TaxonGroup, TaxonomyUpdateProposal, IUCNStatus, Endemism, TaxonGroupTaxonomy
from bims.models.taxonomy import Taxonomy


class EditTaxonView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = 'edit_taxon.html'
    model = Taxonomy
    pk_url_kwarg = 'id'
    fields = [
        'tags',
        'canonical_name',
        'rank',
        'author',
        'iucn_status',
        'parent',
        'taxonomic_status',
        'accepted_taxonomy',
    ]
    success_url = '/taxa_management/'

    def get_object(self, queryset=None):
        taxon = get_object_or_404(
            Taxonomy,
            pk=self.kwargs['id'],
            taxongroup__id=self.kwargs['taxon_group_id']
        )
        proposal = TaxonomyUpdateProposal.objects.filter(
            original_taxonomy=taxon,
            status='pending'
        ).first()
        return proposal or taxon

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rank_choices'] = self.model._meta.get_field('rank').choices
        context['taxon_group_id'] = self.kwargs.get('taxon_group_id', '')
        context['iucn_status_choices'] = IUCNStatus.objects.filter(
            national=False
        ).distinct(
            'order', 'category', 'national'
        )
        context['next'] = self.request.GET.get('next', '')
        context['taxon_ranks'] = [
            {'rank': 'Kingdom', 'field': 'kingdom_name'},
            {'rank': 'Phylum', 'field': 'phylum_name'},
            {'rank': 'Class', 'field': 'class_name'},
            {'rank': 'Order', 'field': 'order_name'},
            {'rank': 'Family', 'field': 'family_name'},
            {'rank': 'Subfamily', 'field': 'sub_family_name'},
            {'rank': 'Tribe', 'field': 'tribe_name'},
            {'rank': 'Subtribe', 'field': 'sub_tribe_name'},
            {'rank': 'Genus', 'field': 'genus_name'},
            {'rank': 'Species', 'field': 'species_name'},
            {'rank': 'Subspecies', 'field': 'sub_species_name'}
        ]
        return context

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        taxon_group = get_object_or_404(
            TaxonGroup,
            pk=self.kwargs['taxon_group_id']
        )
        return taxon_group.experts.filter(
            id=self.request.user.id
        ).exists()

    def is_taxon_edited(self, taxon):
        return TaxonomyUpdateProposal.objects.filter(
            original_taxonomy=taxon,
            status='pending'
        ).exists()

    def form_valid(self, form):
        taxon = form.instance
        if isinstance(taxon, TaxonomyUpdateProposal):
            taxon = taxon.original_taxonomy
        taxon_group_id = self.kwargs.get('taxon_group_id')
        taxon_group = get_object_or_404(TaxonGroup, pk=taxon_group_id)
        taxon_edited = self.is_taxon_edited(taxon)

        if taxon_edited and not is_expert(self.request.user, taxon_group):
            messages.error(self.request, 'Taxon is still being edited')
            return redirect(self.get_success_url())

        data = form.cleaned_data

        data['common_name'] = self.request.POST.get('common_name', '')
        data['tags'] = self.request.POST.getlist('tags')
        data['biographic_distributions'] = (
            self.request.POST.getlist('biographic_distributions')
        )

        data['Taxonomic Comments'] = (
            self.request.POST.get('additional_data__Taxonomic_Comments', '')).strip()
        data['Taxonomic References'] = (
            self.request.POST.get('additional_data__Taxonomic_References', '')).strip()
        data['Biogeographic Comments'] = (
            self.request.POST.get('additional_data__Biogeographic_Comments', '')).strip()
        data['Biogeographic References'] = (
            self.request.POST.get('additional_data__Biogeographic_References', '')).strip()
        data['Environmental Comments'] = (
            self.request.POST.get('additional_data__Environmental_Comments', '')).strip()
        data['Environmental References'] = (
            self.request.POST.get('additional_data__Environmental_References', '')).strip()
        data['Conservation Comments'] = (
            self.request.POST.get('additional_data__Conservation_Comments', '')).strip()
        data['Conservation References'] = (
            self.request.POST.get('additional_data__Conservation_References', '')).strip()

        new_proposal = False

        with transaction.atomic():
            iucn_status = None
            endemism = None
            try:
                iucn_status = IUCNStatus.objects.get(
                    category=data.get('iucn_status'),
                    national=False
                )
            except IUCNStatus.DoesNotExist:
                if taxon.iucn_status:
                    iucn_status = taxon.iucn_status
            except IUCNStatus.MultipleObjectsReturned:
                iucn_status = IUCNStatus.objects.get(
                    category=data.get('iucn_status'),
                    national=False
                ).first()

            try:
                endemism = Endemism.objects.get(name=data.get('endemism'))
            except Endemism.DoesNotExist:
                if taxon.endemism:
                    endemism = taxon.endemism

            proposal = TaxonomyUpdateProposal.objects.filter(
                original_taxonomy=taxon,
                status='pending'
            ).first()

            if not proposal:
                proposal = create_taxon_proposal(
                    taxon=taxon,
                    data=data,
                    taxon_group=taxon_group,
                    iucn_status=iucn_status,
                    endemism=endemism,
                    creator=self.request.user
                )
                TaxonGroupTaxonomy.objects.filter(
                    taxonomy=taxon,
                    taxongroup=taxon_group
                ).update(
                    is_validated=False
                )

                new_proposal = True

                messages.success(
                    self.request,
                    'Taxonomy update proposal created successfully')
            else:
                update_taxon_proposal(
                    proposal=proposal,
                    data=data,
                    iucn_status=iucn_status,
                    endemism=endemism
                )
                messages.success(
                    self.request,
                    'Taxonomy updated successfully')

        # The proposal is automatically approved if the user is a superuser
        if proposal and self.request.user.is_superuser and new_proposal:
            proposal.approve(self.request.user)

        return redirect(self.get_success_url())

    def get_success_url(self):
        next_path = self.request.POST.get('next')
        if next_path:
            return next_path
        return reverse('taxa-management')
