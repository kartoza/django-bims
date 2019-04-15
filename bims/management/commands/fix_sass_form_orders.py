from django.core.management.base import BaseCommand
from bims.utils.logger import log
from sass.models import SassTaxon


TAXON_LIST = [
    'PORIFERA',
    'COELENTERATA',
    'TURBELLARIA',
    'OLIGOCHAETA',
    'HIRUDINEA',
    'AMPHIPODA',
    'POTAMONAUTIDAE',
    'ATYIDAE',
    'PALAEMONIDAE',
    'HYDRACARINA',
    'NOTONEMOURIDAE',
    'PERLIDAE',
    'BAETIDAE 1',
    'BAETIDAE 2',
    'BAETIDAE > 2 SP',
    'CAENIDAE',
    'EPHEMERIDAE',
    'HEPTAGENIIDAE',
    'OLIGONEURIDAE',
    'LEPTOPHLEBIIDAE',
    'POLYMITARCYIDAE',
    'PROSOPISTOMATIDAE',
    'TELOGANODIDAE',
    'TRICORYTHIDAE',
    'CALOPTERYGIDAE',
    'CHLOROCYPHIDAE',
    'SYNLESTIDAE',
    'COENAGRIONIDAE',
    'LESTIDAE',
    'PLATYCNEMIDAE',
    'PROTONEURIDAE',
    'AESHNIDAE',
    'CORDULIIDAE',
    'GOMPHIDAE',
    'LIBELLULIDAE',
    'CRAMBIDAE',
    'BELOSTOMATIDAE',
    'CORIXIDAE',
    'GERRIDAE',
    'HYDROMETRIDAE',
    'NAUCORIDAE',
    'NEPIDAE',
    'NOTONECTIDAE',
    'PLEIDAE',
    'VELIIDAE',
    'CORYDALIDAE',
    'SIALIDAE',
    'DIPSEUDOPSIDAE',
    'ECNOMIDAE',
    'HYDROPSYCHIDAE 1 SP',
    'HYDROPSYCHIDAE 2 SP',
    'HYDROPSYCHIDAE > 2 SP',
    'PHILOPOTAMIDAE',
    'POLYCENTROPODIDAE',
    'PSYCHOMYIIDAE/XIPHOCENTRONIDAE',
    'BARBAROCHTHONIDAE',
    'CALAMOCERATIDAE',
    'GLOSSOSOMATIDAE',
    'HYDROPTILIDAE',
    'HYDROSALPINGIDAE',
    'LEPIDOSTOMATIDAE',
    'LEPTOCERIDAE',
    'PETROTHRINCIDAE',
    'PISULIIDAE',
    'SERICOSTOMATIDAE',
    'DYTISCIDAE',
    'ELMIDAE/DRYOPIDAE',
    'GYRINIDAE',
    'HALIPLIDAE',
    'SCIRTIDAE',
    'HYDRAENIDAE',
    'HYDROPHILIDAE',
    'LIMNICHIDAE',
    'PSEPHENIDAE',
    'ATHERICIDAE',
    'BLEPHARICERIDAE',
    'CERATOPOGONIDAE',
    'CHIRONOMIDAE',
    'CULICIDAE',
    'DIXIDAE',
    'EMPIDIDAE',
    'EPHYDRIDAE',
    'MUSCIDAE',
    'PSYCHODIDAE',
    'SIMULIIDAE',
    'SYRPHIDAE',
    'TABANIDAE',
    'TIPULIDAE',
    'ANCYLIDAE',
    'BULININAE',
    'HYDROBIIDAE',
    'LYMNAEIDAE',
    'PHYSIDAE',
    'PLANORBINAE',
    'THIARIDAE',
    'VIVIPARIDAE',
    'CORBICULIDAE',
    'SPHAERIIDAE',
    'UNIONIDAE',
]


class Command(BaseCommand):
    """Format location context document.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--sass-version',
            dest='sass_version',
            default=5,
            help='Version of SASS')

    def handle(self, *args, **options):
        found_all = True
        sass_version = options.get('sass_version', 5)  # noqa
        sass_taxa = SassTaxon.objects.filter(
            sass_5_score__isnull=False,
            taxon_sass_5__isnull=False
        )

        current_index = 1
        for taxa in TAXON_LIST:
            sass_taxon = sass_taxa.filter(taxon_sass_5__icontains=taxa)
            if not sass_taxon.exists():
                log('This taxa not found : {}'.format(taxa))
                found_all = False
                continue
            else:
                sass_taxon = sass_taxon[0]
                sass_taxon.display_order_sass_5 = current_index
                sass_taxon.save()
                current_index += 1

        log('Found all : {}'.format(found_all))
