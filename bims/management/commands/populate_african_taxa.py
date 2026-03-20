# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Management command to populate African freshwater taxa from GBIF.

Creates taxon groups for Fish, Invertebrates, and Algae, and populates
each with common African freshwater species including full taxonomic hierarchy.
"""
import requests
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.utils import timezone

User = get_user_model()

GBIF_API_BASE = 'https://api.gbif.org/v1'


class Command(BaseCommand):
    help = 'Populate database with common African freshwater taxa from GBIF'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Number of species per group (default: 100)',
        )

    def gbif_species_match(self, name):
        """Match a species name using GBIF backbone API."""
        try:
            response = requests.get(
                f'{GBIF_API_BASE}/species/match',
                params={'name': name, 'strict': False},
                timeout=30,
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.stderr.write(f'    GBIF API error: {e}')
        return None

    def gbif_species_get(self, key):
        """Get species details from GBIF."""
        try:
            response = requests.get(
                f'{GBIF_API_BASE}/species/{key}',
                timeout=30,
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.stderr.write(f'    GBIF API error: {e}')
        return None

    def handle(self, *args, **options):
        limit = options['limit']

        from bims.models import Taxonomy, TaxonGroup, TaxonGroupTaxonomy, IUCNStatus

        # Ensure we have a default site
        site, _ = Site.objects.get_or_create(
            id=1,
            defaults={'domain': 'localhost', 'name': 'BIMS'}
        )

        # Get admin user for approval
        admin = User.objects.filter(is_superuser=True).first()

        self.stdout.write(self.style.NOTICE('Creating taxon groups...'))

        # Create taxon groups
        groups_config = [
            {'name': 'Fish', 'singular_name': 'Fish', 'category': 'SPECIES_MODULE'},
            {'name': 'Invertebrates', 'singular_name': 'Invertebrate', 'category': 'SPECIES_MODULE'},
            {'name': 'Algae', 'singular_name': 'Alga', 'category': 'SPECIES_MODULE'},
        ]

        taxon_groups = {}
        for idx, config in enumerate(groups_config):
            group, created = TaxonGroup.objects.get_or_create(
                name=config['name'],
                defaults={
                    'singular_name': config['singular_name'],
                    'category': config['category'],
                    'site': site,
                    'is_approved': True,
                    'approved_by': admin,
                    'approved_at': timezone.now(),
                    'display_order': idx + 1,
                }
            )
            taxon_groups[config['name']] = group
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f'  {config["name"]}: {status}')

        # IUCN Status categories
        iucn_categories = [
            ('NE', 'Not Evaluated'),
            ('DD', 'Data Deficient'),
            ('LC', 'Least Concern'),
            ('NT', 'Near Threatened'),
            ('VU', 'Vulnerable'),
            ('EN', 'Endangered'),
            ('CR', 'Critically Endangered'),
            ('EW', 'Extinct in the Wild'),
            ('EX', 'Extinct'),
        ]

        self.stdout.write(self.style.NOTICE('Creating IUCN status categories...'))
        for code, name in iucn_categories:
            IUCNStatus.objects.get_or_create(
                category=code,
                defaults={'sensitive': code in ['CR', 'EN', 'VU']}
            )

        # Common African freshwater species by group
        species_lists = {
            'Fish': [
                'Oreochromis niloticus', 'Oreochromis mossambicus', 'Tilapia zillii',
                'Tilapia rendalli', 'Pseudocrenilabrus philander', 'Serranochromis robustus',
                'Labeobarbus aeneus', 'Labeobarbus kimberleyensis', 'Labeobarbus capensis',
                'Labeo umbratus', 'Labeo capensis', 'Barbus anoplus', 'Barbus pallidus',
                'Barbus trimaculatus', 'Enteromius paludinosus', 'Clarias gariepinus',
                'Clarias ngamensis', 'Schilbe intermedius', 'Synodontis zambezensis',
                'Synodontis nigromaculatus', 'Austroglanis sclateri', 'Amphilius uranoscopus',
                'Hydrocynus vittatus', 'Micropterus salmoides', 'Micropterus dolomieu',
                'Oncorhynchus mykiss', 'Salmo trutta', 'Cyprinus carpio', 'Gambusia affinis',
                'Aplocheilichthys johnstoni', 'Nothobranchius rachovii',
                'Marcusenius macrolepidotus', 'Petrocephalus catostoma',
                'Brycinus imberi', 'Protopterus annectens', 'Glossogobius giuris',
                'Ctenopoma multispine', 'Anguilla mossambica', 'Anguilla marmorata',
                'Mesobola brevianalis', 'Astatotilapia calliptera', 'Chetia flaviventris',
                'Labeo cylindricus', 'Labeo molybdinus', 'Labeo rosae', 'Labeo ruddi',
                'Labeo congoro', 'Chiloglanis pretoriae', 'Chiloglanis paratus',
                'Amphilius natalensis', 'Barbus afrohamiltoni', 'Barbus argenteus',
                'Enteromius anoplus', 'Enteromius brevipinnis', 'Enteromius motebensis',
                'Enteromius neefi', 'Labeobarbus marequensis', 'Labeobarbus natalensis',
                'Labeobarbus polylepis', 'Oreochromis andersonii', 'Oreochromis macrochir',
                'Pharyngochromis acuticeps', 'Pseudocrenilabrus philander philander',
                'Sargochromis codringtonii', 'Sargochromis giardi', 'Serranochromis angusticeps',
                'Serranochromis macrocephalus', 'Serranochromis thumbergi', 'Tilapia sparrmanii',
                'Hepsetus odoe', 'Hydrocynus brevis', 'Alestes baremoze', 'Alestes dentex',
                'Brycinus nurse', 'Citharinus citharus', 'Distichodus niloticus',
                'Mormyrus rume', 'Gnathonemus petersii', 'Pollimyrus isidori',
                'Heterobranchus longifilis', 'Bagrus docmak', 'Chrysichthys auratus',
                'Auchenoglanis occidentalis', 'Malapterurus electricus', 'Lates niloticus',
                'Gymnarchus niloticus', 'Polypterus senegalus', 'Polypterus bichir',
                'Protopterus aethiopicus', 'Protopterus dolloi',
            ],
            'Invertebrates': [
                'Baetis harrisoni', 'Caenis sp.', 'Tricorythus discolor',
                'Cheumatopsyche afra', 'Hydropsyche sp.', 'Neoperla spio',
                'Anax imperator', 'Trithemis arteriosa', 'Orthetrum julia',
                'Pseudagrion kersteni', 'Ceriagrion glabrum', 'Africallagma glaucum',
                'Platycypha caligata', 'Chlorolestes fasciatus', 'Anisops sardea',
                'Notonecta sp.', 'Laccotrephes sp.', 'Ranatra sp.', 'Plea sp.',
                'Potamonautes perlatus', 'Potamonautes sidneyi', 'Caridina africana',
                'Bulinus africanus', 'Biomphalaria pfeifferi', 'Lymnaea natalensis',
                'Melanoides tuberculata', 'Physa acuta', 'Burnupia sp.', 'Ferrissia sp.',
                'Tubifex tubifex', 'Hirudo medicinalis', 'Aeshna cyanea',
                'Libellula depressa', 'Ischnura elegans', 'Lestes sponsa',
                'Gomphus vulgatissimus', 'Cordulegaster boltonii', 'Calopteryx virgo',
                'Ephemera danica', 'Heptagenia sulphurea', 'Rhithrogena semicolorata',
                'Limnephilus rhombicus', 'Sericostoma personatum', 'Agapetus fuscipes',
                'Perla bipunctata', 'Leuctra fusca', 'Nemoura cinerea',
                'Gerris lacustris', 'Hydrometra stagnorum', 'Corixa punctata',
                'Sigara striata', 'Dytiscus marginalis', 'Gyrinus natator',
                'Hydrophilus piceus', 'Haliplus ruficollis', 'Chironomus plumosus',
                'Simulium ornatum', 'Tipula oleracea', 'Culex pipiens',
                'Asellus aquaticus', 'Gammarus pulex', 'Daphnia magna',
                'Cyclops strenuus', 'Simocephalus vetulus', 'Ceriodaphnia reticulata',
                'Dugesia tigrina', 'Polycelis nigra', 'Glossiphonia complanata',
                'Erpobdella octoculata', 'Helobdella stagnalis', 'Pisidium casertanum',
                'Sphaerium corneum', 'Anodonta cygnea', 'Unio pictorum',
                'Dreissena polymorpha', 'Theodoxus fluviatilis', 'Bithynia tentaculata',
                'Valvata piscinalis', 'Ancylus fluviatilis', 'Planorbis planorbis',
            ],
            'Algae': [
                'Navicula radiosa', 'Nitzschia palea', 'Gomphonema parvulum',
                'Cymbella affinis', 'Pinnularia viridis', 'Fragilaria capucina',
                'Synedra ulna', 'Melosira varians', 'Cyclotella meneghiniana',
                'Aulacoseira granulata', 'Achnanthes minutissima', 'Cocconeis placentula',
                'Amphora ovalis', 'Surirella angusta', 'Eunotia bilunaris',
                'Tabellaria flocculosa', 'Diatoma vulgare', 'Spirogyra crassa',
                'Cladophora glomerata', 'Oedogonium capillare', 'Stigeoclonium tenue',
                'Mougeotia scalaris', 'Zygnema stellinum', 'Ulothrix zonata',
                'Chlamydomonas reinhardtii', 'Chlorella vulgaris', 'Scenedesmus quadricauda',
                'Pediastrum duplex', 'Coelastrum microporum', 'Ankistrodesmus falcatus',
                'Closterium moniliferum', 'Cosmarium botrytis', 'Staurastrum punctulatum',
                'Micrasterias rotata', 'Anabaena flosaquae', 'Microcystis aeruginosa',
                'Oscillatoria limosa', 'Nostoc commune', 'Phormidium autumnale',
                'Spirulina platensis', 'Aphanizomenon flosaquae', 'Merismopedia glauca',
                'Chroococcus turgidus', 'Euglena gracilis', 'Phacus longicauda',
                'Trachelomonas volvocina', 'Ceratium hirundinella', 'Peridinium cinctum',
                'Dinobryon sertularia', 'Mallomonas caudata', 'Batrachospermum gelatinosum',
                'Asterionella formosa', 'Stephanodiscus hantzschii', 'Gyrosigma acuminatum',
                'Rhopalodia gibba', 'Epithemia sorex', 'Denticula tenuis',
                'Hantzschia amphioxys', 'Stauroneis phoenicenteron', 'Craticula cuspidata',
                'Sellaphora pupula', 'Caloneis silicula', 'Neidium affine',
                'Diploneis elliptica', 'Frustulia rhomboides', 'Staurosira construens',
                'Pseudostaurosira brevistriata', 'Ulnaria ulna', 'Tabularia fasciculata',
                'Rhoicosphenia abbreviata', 'Encyonema minutum', 'Cymatopleura solea',
                'Campylodiscus noricus', 'Surirella brebissonii', 'Nitzschia sigma',
                'Tryblionella hungarica', 'Bacillaria paxillifera', 'Hantzschia virgata',
                'Cylindrotheca closterium', 'Phaeodactylum tricornutum', 'Skeletonema costatum',
                'Chaetoceros muelleri', 'Thalassiosira weissflogii', 'Coscinodiscus radiatus',
            ],
        }

        # Rank hierarchy
        rank_order = ['KINGDOM', 'PHYLUM', 'CLASS', 'ORDER', 'FAMILY', 'GENUS', 'SPECIES']
        rank_keys = {
            'KINGDOM': 'kingdomKey',
            'PHYLUM': 'phylumKey',
            'CLASS': 'classKey',
            'ORDER': 'orderKey',
            'FAMILY': 'familyKey',
            'GENUS': 'genusKey',
            'SPECIES': 'speciesKey',
        }

        def get_or_create_taxonomy(gbif_data, parent=None):
            """Create or get a taxonomy record from GBIF data."""
            gbif_key = gbif_data.get('key') or gbif_data.get('usageKey')
            if not gbif_key:
                return None

            existing = Taxonomy.objects.filter(gbif_key=gbif_key).first()
            if existing:
                return existing

            rank = gbif_data.get('rank', 'SPECIES')
            scientific_name = gbif_data.get('scientificName', '')
            canonical_name = gbif_data.get('canonicalName') or gbif_data.get('species') or scientific_name.split(' (')[0]

            taxonomy = Taxonomy.objects.create(
                scientific_name=scientific_name,
                canonical_name=canonical_name,
                rank=rank,
                gbif_key=gbif_key,
                taxonomic_status=gbif_data.get('taxonomicStatus', 'ACCEPTED'),
                parent=parent,
                author=gbif_data.get('authorship', ''),
                gbif_data=gbif_data,
                validated=True,
            )
            return taxonomy

        def build_taxonomy_hierarchy(match_data):
            """Build full taxonomy hierarchy from GBIF match data."""
            parent = None

            for rank in rank_order[:-1]:  # Exclude SPECIES
                key_name = rank_keys.get(rank)
                if key_name and key_name in match_data:
                    gbif_key = match_data[key_name]

                    existing = Taxonomy.objects.filter(gbif_key=gbif_key).first()
                    if existing:
                        parent = existing
                    else:
                        rank_data = self.gbif_species_get(gbif_key)
                        if rank_data:
                            parent = get_or_create_taxonomy(rank_data, parent)

            # Create species
            species_key = match_data.get('usageKey') or match_data.get('speciesKey')
            if species_key:
                existing = Taxonomy.objects.filter(gbif_key=species_key).first()
                if existing:
                    return existing

                species_data = self.gbif_species_get(species_key)
                if species_data:
                    return get_or_create_taxonomy(species_data, parent)

            return None

        # Process each group
        for group_name, group in taxon_groups.items():
            species_list = species_lists.get(group_name, [])

            self.stdout.write(self.style.NOTICE(f'\nProcessing {group_name}...'))

            added_count = 0
            for species_name in species_list[:limit]:
                self.stdout.write(f'  {species_name}...', ending='')

                try:
                    match = self.gbif_species_match(species_name)

                    if match and match.get('usageKey'):
                        taxonomy = build_taxonomy_hierarchy(match)

                        if taxonomy:
                            TaxonGroupTaxonomy.objects.get_or_create(
                                taxonomy=taxonomy,
                                taxongroup=group,
                                defaults={'is_validated': True},
                            )
                            added_count += 1
                            self.stdout.write(self.style.SUCCESS(' OK'))
                        else:
                            self.stdout.write(self.style.WARNING(' no hierarchy'))
                    else:
                        self.stdout.write(self.style.WARNING(' not found'))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f' error: {e}'))

            self.stdout.write(self.style.SUCCESS(f'  Added {added_count} taxa to {group_name}'))

        total_taxa = Taxonomy.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\nDone! Total taxa in database: {total_taxa}'))
