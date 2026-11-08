(() => {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const enterFort = async scene => {
    const ground = scene.closest('svg').querySelector('.hero-ground');
    const incoming = scene.querySelector('.arrival-incoming');
    const startX = 561;
    const travel = 162;
    const groundLength = ground.getTotalLength();
    const groundY = x => {
      let low = 0;
      let high = groundLength;
      for (let i = 0; i < 20; i++) {
        const distance = (low + high) / 2;
        if (ground.getPointAtLength(distance).x < x) low = distance;
        else high = distance;
      }
      return ground.getPointAtLength((low + high) / 2).y;
    };
    const startY = groundY(startX);
    const doorwayLift = -21.45 - (groundY(startX + travel) - startY);
    const frames = Array.from({length: 81}, (_, i) => {
      const progress = i / 80;
      const x = travel * progress;
      // Blend the last few steps up into the doorway without a position jump.
      const entry = Math.max(0, (progress - .8) / .2);
      const lift = doorwayLift * entry * entry * (3 - 2 * entry);
      const y = groundY(startX + x) - startY + lift;
      return {offset: progress, transform: `translate(${x}px, ${y}px)`};
    });
    scene.classList.replace('arrival-pending', 'arrival-entered');
    // One easing curve for the entire walk, not one restart per waypoint.
    await incoming.animate(frames, {
      duration: 3600,
      easing: 'cubic-bezier(.15, 0, .85, 1)',
      fill: 'forwards'
    }).finished;
    // Disappear into the doorway, then rise behind the fixed battlements.
    await incoming.animate([
      {opacity: 1, transform: 'translate(162px, -21.45px)'},
      {opacity: 0, transform: 'translate(162px, -26px)'}
    ], {duration: 400, easing: 'ease-in', fill: 'forwards'}).finished;
    await scene.querySelector('.arrival-resident').animate([
      {opacity: 1, transform: 'translateY(28px)'},
      {opacity: 1, transform: 'translateY(0)'}
    ], {
      duration: 800,
      delay: 180,
      easing: 'cubic-bezier(.22, 1, .36, 1)',
      fill: 'both'
    }).finished;
  };

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      enterFort(entry.target);
      observer.unobserve(entry.target);
    });
  }, {threshold: .4});
  document.querySelectorAll('.arrival-scene').forEach(scene => {
    scene.classList.add('arrival-pending');
    observer.observe(scene);
  });
})();
