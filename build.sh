#!/usr/bin/env bash
# Assemble the publishable site into ./dist.
# Only these files are public — docs/ and .claude/ stay out.
set -euo pipefail
cd "$(dirname "$0")"

# The early-access button must point somewhere real before anything ships.
if grep -q 'href="EARLY_ACCESS_URL"' index.html; then
  echo "index.html still has the EARLY_ACCESS_URL placeholder; set the early-access link first." >&2
  exit 1
fi

rm -rf dist
mkdir -p dist
cp index.html 404.html styles.css script.js dist/
cp -R assets dist/assets

# Cache-busting: stamp a content hash onto styles.css and script.js so a deploy
# can never leave a browser pairing new HTML with a stale stylesheet.
hash_of() {
  if command -v md5 >/dev/null 2>&1; then md5 -q "$1"; else md5sum "$1" | cut -d' ' -f1; fi
}
css_v=$(hash_of dist/styles.css | cut -c1-10)
js_v=$(hash_of dist/script.js | cut -c1-10)

for page in dist/index.html dist/404.html; do
  sed -i.bak "s|href=\"\(/\{0,1\}\)styles.css\"|href=\"\1styles.css?v=${css_v}\"|" "$page"
  sed -i.bak "s|src=\"script.js\"|src=\"script.js?v=${js_v}\"|" "$page"
done
rm -f dist/*.bak

echo "Built dist/ (css v=${css_v}, js v=${js_v}):"
find dist -type f | sort
