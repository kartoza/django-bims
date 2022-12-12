from rest_framework.response import Response

from bims.models.chem import Chem
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from sass.enums.chem_unit import ChemUnit


class AbioticList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs):
        chem_data = []
        all_chems = Chem.objects.filter(
            show_in_abiotic_list=True
        ).order_by('chem_code')
        for chem in all_chems:
            try:
                chem_unit = ChemUnit[chem.chem_unit].value
            except KeyError:
                chem_unit = chem.chem_unit.unit
            chem_data.append({
                'id': chem.id,
                'description': (
                    chem.chem_description
                    if chem.chem_description else
                    chem.chem_code
                ),
                'unit': chem_unit,
                'max': chem.maximum,
                'min': chem.minimum,
            })
        return Response(chem_data)
