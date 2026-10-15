const viewer = document.querySelector('#image-viewer');
const fullImage = viewer.querySelector('img');
for (const button of document.querySelectorAll('[data-full]')) {
  button.addEventListener('click', () => {
    fullImage.src = button.dataset.full;
    fullImage.alt = button.querySelector('img').alt;
    viewer.showModal();
  });
}
viewer.querySelector('button').addEventListener('click', () => viewer.close());
viewer.addEventListener('click', event => {
  if (event.target === viewer) {
    const rect = viewer.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom) viewer.close();
  }
});

const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const tips = [...document.querySelectorAll('.tip-animation')].map(stage => {
  const tip = { stage, visible: false, playing: false, svg: null, object: null, loopTimer: null };
  tip.play = restart => {
    clearTimeout(tip.loopTimer);
    tip.loopTimer = null;
    tip.playing = true;
    if (!tip.object) {
      const object = document.createElement('object');
      object.type = 'image/svg+xml';
      object.className = 'tip-vector';
      object.setAttribute('aria-label', stage.querySelector('p').textContent);
      object.tabIndex = -1;
      object.addEventListener('load', () => {
        const svg = object.contentDocument?.documentElement;
        if (!svg || typeof svg.pauseAnimations !== 'function') {
          stage.querySelector('small').textContent = 'Animation unavailable'; tip.pause(); return;
        }
        tip.svg = svg;
        svg.pauseAnimations();
        svg.setCurrentTime(0);
        stage.classList.add('has-vector');
        if (tip.playing && tip.visible && !document.hidden) tip.play(false);
      });
      object.data = `home-assets/${stage.dataset.tip}.svg`;
      stage.append(object);
      tip.object = object;
      return;
    }
    if (!tip.svg) return;
    if (restart || tip.svg.getCurrentTime() >= Number(tip.svg.dataset.duration)) tip.svg.setCurrentTime(0);
    tip.svg.unpauseAnimations();
    tip.playing = true;
  };
  tip.pause = () => {
    clearTimeout(tip.loopTimer);
    tip.loopTimer = null;
    tip.svg?.pauseAnimations();
    tip.playing = false;
  };
  return tip;
});
const tipObserver = new IntersectionObserver(entries => {
  for (const entry of entries) {
    const tip = tips.find(tip => tip.stage === entry.target);
    tip.visible = entry.isIntersecting;
    if (!tip.visible) tip.pause();
    else if (!reducedMotion.matches && !document.hidden) tip.play(false);
  }
}, { threshold: 0.35 });
for (const tip of tips) tipObserver.observe(tip.stage);
document.addEventListener('visibilitychange', () => {
  if (document.hidden) for (const tip of tips) tip.pause();
  else if (!reducedMotion.matches) for (const tip of tips) if (tip.visible) tip.play(false);
});
reducedMotion.addEventListener('change', () => {
  if (reducedMotion.matches) for (const tip of tips) tip.pause();
  else for (const tip of tips) if (tip.visible && !document.hidden) tip.play(false);
});
setInterval(() => {
  for (const tip of tips) {
    if (!tip.playing || !tip.svg || tip.loopTimer || tip.svg.getCurrentTime() < Number(tip.svg.dataset.duration)) continue;
    tip.svg.pauseAnimations();
    if (reducedMotion.matches) { tip.pause(); continue; }
    tip.loopTimer = setTimeout(() => {
      tip.loopTimer = null;
      if (tip.visible && !document.hidden) tip.play(true);
    }, 1500);
  }
}, 250);
