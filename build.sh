#!/usr/bin/env bash
# Assemble only public site files; internal docs/*.md stay out.
set -euo pipefail
cd "$(dirname "$0")"

if grep -q 'href="EARLY_ACCESS_URL"' index.html; then
  echo "index.html still has the EARLY_ACCESS_URL placeholder; set the early-access link first." >&2
  exit 1
fi

rm -rf dist
mkdir -p dist/docs
cp index.html 404.html styles.css script.js warden.css warden.js arrivals.js additions.css dist/
cp docs/index.html docs/docs.css docs/docs.js dist/docs/
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
