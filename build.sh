#!/usr/bin/env bash
# Assemble only public site files; internal docs/*.md stay out.
set -euo pipefail
cd "$(dirname "$0")"

if grep -q 'href="EARLY_ACCESS_URL"' index.html; then
  echo "index.html still has the EARLY_ACCESS_URL placeholder; set the early-access link first." >&2
  exit 1
fi

rm -rf dist
mkdir -p dist/docs/aws dist/docs/gcp dist/docs/oci dist/docs/tools dist/docs/understand dist/docs/deploy dist/docs/policy dist/docs/operations
cp index.html 404.html styles.css script.js warden.css warden.js arrivals.js additions.css dist/
cp docs/index.html docs/docs.css docs/docs.js dist/docs/
mkdir -p dist/docs/{aws,gcp,oci,tools}/reference dist/downloads
cp downloads/fort-terraform-customer.zip downloads/fort-terraform-customer.zip.sha256 dist/downloads/
for page in aws gcp oci tools; do cp "docs/$page/reference/index.html" "dist/docs/$page/reference/"; done
cp docs/aws/index.html dist/docs/aws/
cp docs/gcp/index.html dist/docs/gcp/
cp docs/oci/index.html dist/docs/oci/
cp docs/tools/index.html dist/docs/tools/
for page in understand deploy policy operations; do cp "docs/$page/index.html" "dist/docs/$page/"; done
cp -R assets dist/assets

hash_of() {
  if command -v md5 >/dev/null 2>&1; then md5 -q "$1"; else md5sum "$1" | cut -d' ' -f1; fi
}

# Stamp shared and page-specific assets, including references from /docs/.
for asset in styles.css script.js warden.css warden.js arrivals.js additions.css docs/docs.css docs/docs.js assets/fort.svg assets/favicon.svg; do
  version=$(hash_of "dist/$asset" | cut -c1-10)
  asset_name=${asset##*/}
  while IFS= read -r -d '' page; do
    sed -i.bak "s|${asset_name}\"|${asset_name}?v=${version}\"|g" "$page"
    rm -f "$page.bak"
  done < <(find dist -name '*.html' -print0)
done

echo 'Built public landing page, documentation and assets:'
find dist -type f | sort
