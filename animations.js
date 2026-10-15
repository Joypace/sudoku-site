export function observeAnimations(root = document) {
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const tips = [...root.querySelectorAll('.tip-animation')].map(stage => {
  const source = () => stage.dataset.mobileSrc && matchMedia('(max-width: 680px)').matches ? stage.dataset.mobileSrc : stage.dataset.src || `home-assets/${stage.dataset.tip}.svg`;
  const tip = { stage, visible: false, playing: false, svg: null, object: null, loopTimer: null };
  tip.play = restart => {
    if (stage.closest('details')?.open === false) return;
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
        if (tip.object !== object) return;
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
      object.data = source();
      stage.append(object);
      tip.object = object;
      return;
    }
    if (!tip.svg) return;
    if (Number(tip.svg.dataset.duration) <= 0) {
      tip.svg.pauseAnimations();
      tip.playing = false;
      return;
    }
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
  if (stage.dataset.mobileSrc) {
    matchMedia('(max-width: 680px)').addEventListener('change', () => {
      tip.pause();
      tip.object?.remove();
      tip.object = tip.svg = null;
      stage.classList.remove('has-vector');
      if (tip.visible && !reducedMotion.matches && !document.hidden) tip.play(true);
    });
  }
  const disclosure = stage.closest('details');
  disclosure?.addEventListener('toggle', () => {
    if (!disclosure.open) {
      tip.pause();
      tip.object?.remove();
      tip.object = tip.svg = null;
      stage.classList.remove('has-vector');
    }
  });
  return tip;
});
const tipObserver = new IntersectionObserver(entries => {
  for (const entry of entries) {
    const tip = tips.find(tip => tip.stage === entry.target);
    tip.visible = entry.isIntersecting && entry.intersectionRatio >= 0.35;
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

}
