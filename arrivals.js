(() => {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const scenes = document.querySelectorAll('.arrival-scene');
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.replace('arrival-pending','arrival-entered');
      observer.unobserve(entry.target);
    });
  },{threshold:.4});
  scenes.forEach(scene => {
    scene.classList.add('arrival-pending');
    observer.observe(scene);
  });
})();
