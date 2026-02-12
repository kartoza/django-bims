"""Taxa validation script for validating CSV uploads without importing.

This script validates taxa CSV files for:
- Duplicate GBIF keys within the file
- Duplicate FADA IDs within the file
- Existing GBIF keys in the database
- Existing FADA IDs in the database
- GBIF key validation against GBIF API (rank and taxon name)
"""
import csv
import copy
import difflib
import logging
from io import StringIO
from collections import defaultdict

from bims.scripts.species_keys import GBIF_LINK, GBIF_URL, FADA_ID, TAXON, TAXON_RANK, GENUS, SPECIES
from bims.scripts.data_upload import FALLBACK_ENCODINGS
from bims.models import Taxonomy, UploadSession
from bims.utils.domain import get_current_domain
from bims.utils.gbif import get_species

logger = logging.getLogger('bims')

VALIDATION_OK = '_validation_ok'
VALIDATION_WARNING = '_validation_warning'
VALIDATION_ERROR = '_validation_error'
NAME_SIMILARITY_THRESHOLD = 1


class TaxaValidator:
    """Validates taxa data without creating records."""

    def __init__(self, upload_session):
        self.upload_session = upload_session
        self.file_gbif_keys = defaultdict(list)  # {gbif_key: [row_numbers]}
        self.file_fada_ids = defaultdict(list)   # {fada_id: [row_numbers]}
        self.file_taxon_name_rank = defaultdict(list)  # {(name_lower, rank_upper): [row_numbers]}
        self.validation_results = []  # List of (row_dict, status_messages)
        self.all_rows = []
        self.headers = []
        self.total_rows = 0
        self.domain = get_current_domain()

    @staticmethod
    def row_value(row, key):
        """Get cleaned value from row."""
        value = row.get(key, '')
        if value:
            value = str(value).strip()
        return value

    def _extract_gbif_key(self, row):
        """Extract GBIF key from GBIF_LINK or GBIF_URL column."""
        gbif_link = self.row_value(row, GBIF_LINK) or self.row_value(row, GBIF_URL)
        if gbif_link:
            last = str(gbif_link).rstrip('/').split('/')[-1]
            return last[:-2] if last.endswith('.0') else last
        return None

    def _check_database_duplicates(self, gbif_key, fada_id):
        """Check if record already exists in database. Returns list of warnings."""
        warnings = []
        if gbif_key:
            try:
                gbif_taxa = Taxonomy.objects.filter(gbif_key=int(gbif_key))
                warning_message = ''
                if gbif_taxa.exists():
                    warning_message = f"WARNING: GBIF key {gbif_key} already exists in database:"
                for _taxon in gbif_taxa:
                    warning_message += (
                        f"{_taxon.canonical_name} ({_taxon.rank}) "
                    )
                if warning_message:
                    warnings.append(warning_message)
            except (ValueError, TypeError):
                pass
        if fada_id:
            fada_taxa = Taxonomy.objects.filter(fada_id=fada_id)
            warning_message = ''
            if fada_taxa.exists():
                warning_message = f"WARNING: FADA ID {fada_id} already exists in database:"
            for _taxon in fada_taxa:
                warning_message += (
                    f"{_taxon.canonical_name} ({_taxon.rank}) "
                )
            if warning_message:
                warnings.append(warning_message)
        return warnings

    def _normalize_name(self, name):
        """Normalize taxon name for comparison."""
        if not name:
            return ''
        return ' '.join(name.lower().split())

    def _get_input_taxon_name(self, row):
        """Get the taxon name from the row, composing it if necessary."""
        taxon = self.row_value(row, TAXON)
        if taxon:
            return taxon

        genus = self.row_value(row, GENUS)
        species = self.row_value(row, SPECIES)
        if genus and species:
            return f"{genus} {species}"
        elif genus:
            return genus

        return ''

    def _validate_gbif_key(self, row, gbif_key):
        """Validate GBIF key against GBIF API. Returns list of messages."""
        messages = []

        if not gbif_key:
            return messages

        try:
            gbif_key_int = int(gbif_key)
        except (ValueError, TypeError):
            messages.append(f"ERROR: Invalid GBIF key format: {gbif_key}")
            return messages

        try:
            gbif_rec = get_species(gbif_key_int)
        except Exception as e:
            messages.append(f"WARNING: GBIF lookup failed for key {gbif_key}: {str(e)}")
            return messages

        if not gbif_rec or not isinstance(gbif_rec, dict) or not gbif_rec.get("key"):
            messages.append(f"WARNING: GBIF record not found for key {gbif_key}")
            return messages

        input_rank = self.row_value(row, TAXON_RANK).upper() if self.row_value(row, TAXON_RANK) else ''
        input_name = self._get_input_taxon_name(row)

        gbif_rank = (gbif_rec.get("rank") or '').upper()
        gbif_name = gbif_rec.get("canonicalName") or gbif_rec.get("scientificName") or ""

        # Check rank mismatch - ERROR
        if input_rank and gbif_rank and input_rank != gbif_rank:
            messages.append(
                f"ERROR: GBIF key {gbif_key} refers to a different taxon. "
                f"Expected rank '{input_rank}' but GBIF returns '{gbif_rank}' for '{gbif_name}'"
            )

        # Check name mismatch - WARNING
        if input_name and gbif_name:
            norm_input = self._normalize_name(input_name)
            norm_gbif = self._normalize_name(gbif_name)

            if norm_input != norm_gbif:
                # Calculate similarity
                similarity = difflib.SequenceMatcher(None, norm_input, norm_gbif).ratio()

                if similarity < NAME_SIMILARITY_THRESHOLD:
                    messages.append(
                        f"ERROR: GBIF key {gbif_key} may refer to a different taxon. "
                        f"Input name '{input_name}' does not match GBIF name '{gbif_name}' "
                        f"(similarity: {similarity:.0%})"
                    )

        return messages

    def _first_pass_collect_keys(self, rows):
        """First pass: collect all GBIF keys, FADA IDs, and taxon names to detect duplicates."""
        for row_number, row in enumerate(rows, start=2):  # Start at 2 (row 1 is header)
            gbif_key = self._extract_gbif_key(row)
            fada_id = self.row_value(row, FADA_ID)
            taxon_name = self._get_input_taxon_name(row)
            taxon_rank = self.row_value(row, TAXON_RANK)

            if gbif_key:
                self.file_gbif_keys[gbif_key].append(row_number)
            if fada_id:
                self.file_fada_ids[fada_id].append(row_number)
            if taxon_name:
                # Store as (name_lower, rank_upper) tuple for comparison
                name_rank_key = (taxon_name.lower(), (taxon_rank or '').upper())
                self.file_taxon_name_rank[name_rank_key].append(row_number)

    def _validate_row(self, row, row_number):
        """Validate a single row. Returns list of error/warning messages."""
        messages = []

        gbif_key = self._extract_gbif_key(row)
        fada_id = self.row_value(row, FADA_ID)

        # Check for within-file duplicates (GBIF key)
        if gbif_key and len(self.file_gbif_keys.get(gbif_key, [])) > 1:
            other_rows = [r-1 for r in self.file_gbif_keys[gbif_key] if r != row_number]
            messages.append(
                f"ERROR: Duplicate GBIF key {gbif_key} (also in row(s) {', '.join(map(str, other_rows))})"
            )

        # Check for within-file duplicates (FADA ID)
        if fada_id and len(self.file_fada_ids.get(fada_id, [])) > 1:
            other_rows = [r-1 for r in self.file_fada_ids[fada_id] if r != row_number]
            messages.append(
                f"ERROR: Duplicate FADA ID {fada_id} (also in row(s) {', '.join(map(str, other_rows))})"
            )

        # Check for within-file duplicates (same taxon name + same rank = ERROR)
        taxon_name = self._get_input_taxon_name(row)
        taxon_rank = self.row_value(row, TAXON_RANK)
        if taxon_name:
            name_rank_key = (taxon_name.lower(), (taxon_rank or '').upper())
            if len(self.file_taxon_name_rank.get(name_rank_key, [])) > 1:
                other_rows = [r - 1 for r in self.file_taxon_name_rank[name_rank_key] if r != row_number]
                messages.append(
                    f"ERROR: Duplicate taxon name '{taxon_name}' with same rank '{taxon_rank}' "
                    f"(also in row(s) {', '.join(map(str, other_rows))})"
                )

        # Check database duplicates
        db_warnings = self._check_database_duplicates(gbif_key, fada_id)
        messages.extend(db_warnings)

        # Validate GBIF key against GBIF API (rank and name check)
        gbif_validation = self._validate_gbif_key(row, gbif_key)
        messages.extend(gbif_validation)

        return messages

    def validate_file(self):
        """Validate the CSV file from the upload session."""
        try:
            with open(self.upload_session.process_file.path, 'rb') as fh:
                raw = fh.read()
        except Exception as e:
            self.upload_session.error_notes = f"Error reading file: {e}"
            self.upload_session.canceled = True
            self.upload_session.save()
            return

        # Try different encodings
        tried = ["utf-8-sig"] + [e for e in FALLBACK_ENCODINGS if e != "utf-8-sig"]
        text = None
        last_exc = None
        for enc in tried:
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError as exc:
                last_exc = exc
                continue

        if text is None:
            self.upload_session.error_notes = (
                f"Could not decode file with encodings {tried}: {last_exc}"
            )
            self.upload_session.canceled = True
            self.upload_session.save()
            return

        try:
            reader = csv.DictReader(StringIO(text))
            self.headers = reader.fieldnames or []
            self.all_rows = list(reader)
            self.total_rows = len(self.all_rows)
        except Exception as e:
            self.upload_session.error_notes = f"Error parsing CSV: {e}"
            self.upload_session.canceled = True
            self.upload_session.save()
            return

        # Update progress
        self.upload_session.progress = f"0/{self.total_rows}"
        self.upload_session.save()

        # First pass: collect all keys
        self._first_pass_collect_keys(self.all_rows)

        # Second pass: validate each row
        for index, row in enumerate(self.all_rows):
            if UploadSession.objects.get(id=self.upload_session.id).canceled:
                return

            row_number = index + 2
            messages = self._validate_row(row, row_number)

            # Separate errors and warnings
            errors = [m for m in messages if m.startswith('ERROR:')]
            warnings = [m for m in messages if m.startswith('WARNING:')]

            # Set validation columns
            if errors:
                row[VALIDATION_ERROR] = '; '.join(errors)
            else:
                row[VALIDATION_ERROR] = ''

            if warnings:
                row[VALIDATION_WARNING] = '; '.join(warnings)
            else:
                row[VALIDATION_WARNING] = ''

            # Set OK status only if no errors and no warnings
            if not errors and not warnings:
                row[VALIDATION_OK] = 'OK'
            else:
                row[VALIDATION_OK] = ''

            self.validation_results.append(row)

            # Update progress
            self.upload_session.progress = f"{index + 1}/{self.total_rows}"
            self.upload_session.save()

        # Generate validated CSV
        self._generate_validated_csv()

    def _generate_validated_csv(self):
        """Generate the validated CSV with _validation_status column."""
        file_name = self.upload_session.process_file.name.replace('taxa-file/', '')
        file_path = self.upload_session.process_file.path.replace(file_name, '')

        # Add validation status to headers
        output_headers = copy.deepcopy(self.headers)
        if VALIDATION_ERROR not in output_headers:
            output_headers.append(VALIDATION_ERROR)
        if VALIDATION_WARNING not in output_headers:
            output_headers.append(VALIDATION_WARNING)
        if VALIDATION_OK not in output_headers:
            output_headers.append(VALIDATION_OK)

        validated_file_path = f'{file_path}validated_{file_name}'

        with open(validated_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=output_headers,
                quoting=csv.QUOTE_MINIMAL,
                extrasaction='ignore'
            )
            writer.writeheader()
            for row in self.validation_results:
                writer.writerow(row)

        # Save to error_file field (reusing this field for the validated output)
        self.upload_session.error_file.name = f'taxa-file/validated_{file_name}'

        # Count errors and warnings
        error_count = sum(1 for r in self.validation_results if r.get(VALIDATION_ERROR))
        warning_count = sum(1 for r in self.validation_results if r.get(VALIDATION_WARNING))
        ok_count = sum(1 for r in self.validation_results if r.get(VALIDATION_OK) == 'OK')

        self.upload_session.progress = f"Validation complete: {ok_count} OK, {error_count} errors, {warning_count} warnings"
        self.upload_session.processed = True
        self.upload_session.save()
