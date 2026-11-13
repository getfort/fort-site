// Preserve links to the original single-page reference.
const legacyTopics = {
  overview: 'understand', pillars: 'understand', sandbox: 'understand',
  deployment: 'deploy', policies: 'policy', approvals: 'policy',
  evidence: 'operations', agents: 'operations', roadmap: 'operations'
};
const isDocsHome = /\/docs\/(?:index\.html)?$/.test(location.pathname);
function routeLegacyTopic() {
  const topic = location.hash.slice(1);
  if (isDocsHome && Object.hasOwn(legacyTopics, topic)) {
    location.replace(new URL(`${legacyTopics[topic]}/#${topic}`, location.href));
  }
}
routeLegacyTopic();
addEventListener('hashchange', routeLegacyTopic);

const navigation = document.querySelector('.docs-navigation');
const compact = matchMedia('(max-width: 760px)');
function sizeNavigation() {
  if (navigation) navigation.open = !compact.matches;
}
sizeNavigation();
compact.addEventListener('change', sizeNavigation);

const docLinks = [...document.querySelectorAll('.page-contents a')];
const sections = docLinks.map(link => document.getElementById(link.hash.slice(1))).filter(Boolean);
function updateLocation() {
  const active = sections.filter(section => section.getBoundingClientRect().top <= 180).at(-1) || sections[0];
  if (!active) return;
  docLinks.forEach(link => {
    if (link.hash === '#' + active.id) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
}
let scheduled = false;
addEventListener('scroll', () => {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(() => { updateLocation(); scheduled = false; });
}, {passive: true});
updateLocation();
