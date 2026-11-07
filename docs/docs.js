const docLinks = [...document.querySelectorAll('.docs-sidebar nav a')];
const sections = docLinks.map(link => document.querySelector(link.getAttribute('href')));
function updateLocation() {
  const active = sections.filter(section => section.getBoundingClientRect().top <= 160).at(-1) || sections[0];
  docLinks.forEach(link => {
    if (link.hash === '#' + active.id) link.setAttribute('aria-current','location');
    else link.removeAttribute('aria-current');
  });
}
let scheduled = false;
addEventListener('scroll',()=> {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(()=> {updateLocation();scheduled = false;});
},{passive:true});
updateLocation();
