# coding=utf-8
import csv
import io
import zipfile
from pathlib import Path

from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)
from rest_framework.views import APIView

from bims.api_views.merge_sites import IsSuperUser

FALLBACK_ENCODINGS = ('utf-8-sig', 'utf-8', 'latin-1')


def _read_occurrence_file(uploaded_file):
    file_name = Path(uploaded_file.name or "").name.lower()
    file_bytes = uploaded_file.read()

    if file_name == "occurrence.txt":
        return file_bytes, None

    if file_name.endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                if "occurrence.txt" not in zf.namelist():
                    return None, "occurrence.txt not found in the ZIP archive."

                try:
                    return zf.read("occurrence.txt"), None
                except Exception as exc:
                    return None, f"Could not read occurrence.txt: {exc}"
        except zipfile.BadZipFile:
            return None, "Uploaded file is not a valid ZIP archive."

    return None, "Please upload a GBIF DwC-A ZIP archive or occurrence.txt file."


class UpdateCustodianFromGbifArchive(APIView):
    """Accept a GBIF DwC-A zip or occurrence.txt file and update institution_id
    on occurrence records from the institutionCode column in occurrence.txt.

    The occurrenceID column uses the format ``{schema_name}:{uuid}``;
    only the UUID part is used for matching.
    """

    permission_classes = (IsSuperUser,)

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response(
                {"error": "Permission denied."},
                status=HTTP_403_FORBIDDEN,
            )

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"error": "No file uploaded."},
                status=HTTP_400_BAD_REQUEST,
            )

        occ_bytes, error = _read_occurrence_file(uploaded_file)
        if error:
            return Response(
                {"error": error},
                status=HTTP_400_BAD_REQUEST,
            )

        text = None
        for enc in FALLBACK_ENCODINGS:
            try:
                text = occ_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            return Response(
                {"error": "Could not decode occurrence.txt."},
                status=HTTP_400_BAD_REQUEST,
            )

        reader = csv.DictReader(io.StringIO(text), delimiter="\t")

        fieldnames = reader.fieldnames or []
        if "occurrenceID" not in fieldnames:
            return Response(
                {"error": "occurrence.txt is missing the occurrenceID column."},
                status=HTTP_400_BAD_REQUEST,
            )
        if "institutionCode" not in fieldnames:
            return Response(
                {"error": "occurrence.txt is missing the institutionCode column."},
                status=HTTP_400_BAD_REQUEST,
            )

        from bims.models.biological_collection_record import BiologicalCollectionRecord
        from bims.signals.utils import disconnect_bims_signals, connect_bims_signals

        updated = 0
        skipped = 0

        disconnect_bims_signals()
        try:
            for row in reader:
                occurrence_id = (row.get("occurrenceID") or "").strip()
                inst_code = (row.get("institutionCode") or "").strip()

                if not occurrence_id or not inst_code:
                    skipped += 1
                    continue

                # occurrenceID format: {schema_name}:{uuid}
                uuid_val = occurrence_id.split(":", 1)[-1]

                try:
                    record = BiologicalCollectionRecord.objects.get(uuid=uuid_val)
                except BiologicalCollectionRecord.DoesNotExist:
                    skipped += 1
                    continue
                except BiologicalCollectionRecord.MultipleObjectsReturned:
                    skipped += 1
                    continue
                except Exception:
                    skipped += 1
                    continue

                if record.institution_id == inst_code:
                    skipped += 1
                    continue

                record.institution_id = inst_code
                record.save(update_fields=["institution_id"])
                updated += 1
        finally:
            connect_bims_signals()

        return Response(
            {
                "message": (
                    f"Custodian updated for {updated} occurrence(s). "
                    f"{skipped} skipped."
                ),
                "updated": updated,
                "skipped": skipped,
            },
            status=HTTP_200_OK,
        )
