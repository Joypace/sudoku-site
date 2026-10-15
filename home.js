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
  const toggle = stage.nextElementSibling.querySelector('[data-tip-action="toggle"]');
  const replay = stage.nextElementSibling.querySelector('[data-tip-action="replay"]');
  const status = stage.nextElementSibling.querySelector('.tip-status');
  const tip = { stage, toggle, status, visible: false, playing: false, userPaused: false, svg: null, object: null, loopTimer: null };
  tip.play = restart => {
    clearTimeout(tip.loopTimer);
    tip.loopTimer = null;
    tip.userPaused = false;
    tip.playing = true;
    toggle.textContent = 'Pause animation';
    toggle.setAttribute('aria-pressed', 'true');
    if (!tip.object) {
      const object = document.createElement('object');
      object.type = 'image/svg+xml';
      object.className = 'tip-vector';
      object.setAttribute('aria-label', stage.querySelector('p').textContent);
      object.tabIndex = -1;
      object.addEventListener('load', () => {
        const svg = object.contentDocument?.documentElement;
        if (!svg || typeof svg.pauseAnimations !== 'function') {
          status.textContent = 'Animation unavailable'; tip.pause(); return;
        }
        tip.svg = svg;
        svg.pauseAnimations();
        svg.setCurrentTime(0);
        stage.classList.add('has-vector');
        if (tip.playing && tip.visible && !document.hidden && !tip.userPaused) tip.play(false);
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
    toggle.textContent = 'Pause animation';
    toggle.setAttribute('aria-pressed', 'true');
  };
  tip.pause = () => {
    clearTimeout(tip.loopTimer);
    tip.loopTimer = null;
    tip.svg?.pauseAnimations();
    tip.playing = false;
    toggle.textContent = 'Play animation';
    toggle.setAttribute('aria-pressed', 'false');
  };
  toggle.addEventListener('click', () => {
    if (tip.playing) { tip.userPaused = true; tip.pause(); }
    else tip.play(false);
  });
  replay.addEventListener('click', () => tip.play(true));
  return tip;
});
const tipObserver = new IntersectionObserver(entries => {
  for (const entry of entries) {
    const tip = tips.find(tip => tip.stage === entry.target);
    tip.visible = entry.isIntersecting;
    if (!tip.visible) tip.pause();
    else if (!reducedMotion.matches && !tip.userPaused && !document.hidden) tip.play(false);
  }
}, { threshold: 0.35 });
for (const tip of tips) tipObserver.observe(tip.stage);
document.addEventListener('visibilitychange', () => {
  if (document.hidden) for (const tip of tips) tip.pause();
  else if (!reducedMotion.matches) for (const tip of tips) if (tip.visible && !tip.userPaused) tip.play(false);
});
reducedMotion.addEventListener('change', () => {
  if (reducedMotion.matches) for (const tip of tips) tip.pause();
  else for (const tip of tips) if (tip.visible && !tip.userPaused && !document.hidden) tip.play(false);
});
setInterval(() => {
  for (const tip of tips) {
    if (!tip.playing || !tip.svg || tip.loopTimer || tip.svg.getCurrentTime() < Number(tip.svg.dataset.duration)) continue;
    tip.svg.pauseAnimations();
    if (reducedMotion.matches) { tip.pause(); continue; }
    tip.loopTimer = setTimeout(() => {
      tip.loopTimer = null;
      if (tip.visible && !document.hidden && !tip.userPaused) tip.play(true);
    }, 1500);
  }
}, 250);
