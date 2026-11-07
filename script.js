const menu = document.querySelector('.menu-toggle');
const mobileNav = document.querySelector('#mobile-nav');
menu.addEventListener('click', () => {
  const open = menu.getAttribute('aria-expanded') !== 'true';
  menu.setAttribute('aria-expanded', String(open));
  menu.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
  mobileNav.hidden = !open;
});
function closeMenu() {
  menu.setAttribute('aria-expanded', 'false');
  menu.setAttribute('aria-label', 'Open navigation');
  mobileNav.hidden = true;
}
mobileNav.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !mobileNav.hidden) {
    closeMenu();
    menu.focus();
  }
});
const policyToggle = document.querySelector('#policy-toggle');
policyToggle.addEventListener('click', event => {
  event.preventDefault();
  const open = policyToggle.getAttribute('aria-expanded') !== 'true';
  policyToggle.setAttribute('aria-expanded', String(open));
  document.querySelector('#policy-detail').hidden = !open;
  policyToggle.querySelector('span').textContent = open ? '−' : '+';
});
const replay = document.querySelector('#replay');
const rows = [...document.querySelectorAll('.decision-row')];
const status = document.querySelector('#demo-status');
const messages = ['Read allowed by policy.', 'Restart held for human approval.', 'Deletion denied by policy.'];
replay.addEventListener('click', async () => {
  replay.disabled = true;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  rows.forEach(row => row.classList.add('waiting'));
  for (const [index, row] of rows.entries()) {
    row.classList.remove('waiting');
    row.classList.add('active');
    status.textContent = messages[index];
    await new Promise(resolve => setTimeout(resolve, reducedMotion ? 250 : 950));
    row.classList.remove('active');
  }
  status.textContent = 'Three decisions. All recorded.';
  replay.disabled = false;
});
