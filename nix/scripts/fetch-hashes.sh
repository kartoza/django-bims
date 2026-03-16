#!/usr/bin/env bash
# Helper script to fetch package hashes from PyPI for Nix derivations
# Usage: ./fetch-hashes.sh
#
# This script fetches the SHA256 hashes for all custom Python packages
# and outputs them in a format suitable for Nix.

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to get package hash from PyPI
get_pypi_hash() {
    local pname="$1"
    local version="$2"

    # Try to fetch the package info from PyPI
    local url="https://pypi.org/pypi/${pname}/${version}/json"
    local response

    response=$(curl -sf "$url" 2>/dev/null) || {
        echo "FAILED"
        return 1
    }

    # Extract the sha256 hash for the source distribution
    local hash
    hash=$(echo "$response" | jq -r '.urls[] | select(.packagetype == "sdist") | .digests.sha256' 2>/dev/null | head -1)

    if [ -z "$hash" ] || [ "$hash" = "null" ]; then
        # Try wheel if no sdist
        hash=$(echo "$response" | jq -r '.urls[] | select(.packagetype == "bdist_wheel") | .digests.sha256' 2>/dev/null | head -1)
    fi

    if [ -z "$hash" ] || [ "$hash" = "null" ]; then
        echo "FAILED"
        return 1
    fi

    # Convert to SRI format
    echo "sha256-$(echo "$hash" | xxd -r -p | base64 | tr -d '\n')"
}

echo "Fetching package hashes from PyPI..."
echo ""

# List of packages (pname:version)
PACKAGES=(
    "django-admin-inline-paginator:0.4.0"
    "django-admin-rangefilter:0.13.3"
    "django-braces:1.14.0"
    "django-colorfield:0.9.0"
    "django-contact-us:0.4.3"
    "django-cryptography:1.1"
    "django-easy-audit:1.3.9a1"
    "django-forms-bootstrap:3.1.0"
    "django-grappelli:4.0.3"
    "django-imagekit:4.0.2"
    "django-invitations:2.0.0"
    "django-modelsdoc:0.1.11"
    "django-ordered-model:3.7.4"
    "django-preferences:1.0.0"
    "django-role-permissions:2.2.1"
    "django-uuid-upload-path:1.0.0"
    "djangorestframework-gis:1.0"
    "dj-pagination:2.5.0"
    "eutils:0.6.0"
    "pygbif:0.6.0"
    "python-dwca-reader:0.16.0"
    "raven:6.10.0"
)

echo "# Package hashes for nix/packages/python/"
echo "# Generated on $(date)"
echo ""

for pkg in "${PACKAGES[@]}"; do
    pname="${pkg%%:*}"
    version="${pkg##*:}"

    printf "%-35s " "$pname ($version):"
    hash=$(get_pypi_hash "$pname" "$version")

    if [ "$hash" = "FAILED" ]; then
        printf "${RED}%s${NC}\n" "FAILED - check package name/version"
    else
        printf "${GREEN}%s${NC}\n" "$hash"
    fi
done

echo ""
echo "Note: geonode-oauth-toolkit uses fetchFromGitHub, fetch hash with:"
echo "  nix-prefetch-github GeoNode geonode-oauth-toolkit --rev v2.2.2"
