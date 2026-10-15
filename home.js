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
  const svg = stage.querySelector('svg');
  const controls = stage.nextElementSibling;
  const toggle = controls.querySelector('[data-tip-action="toggle"]');
  const replay = controls.querySelector('[data-tip-action="replay"]');
  svg.pauseAnimations();
  svg.setCurrentTime(0);
  const tip = { stage, svg, toggle, duration: Number(svg.dataset.duration), visible: false, userPaused: false, playing: false };
  tip.setPlaying = playing => {
    tip.playing = playing;
    playing ? svg.unpauseAnimations() : svg.pauseAnimations();
    toggle.textContent = playing ? 'Pause animation' : 'Play animation';
    toggle.setAttribute('aria-pressed', String(playing));
  };
  toggle.addEventListener('click', () => {
    tip.userPaused = tip.playing;
    if (svg.getCurrentTime() >= tip.duration) svg.setCurrentTime(0);
    tip.setPlaying(!tip.playing);
  });
  replay.addEventListener('click', () => {
    svg.setCurrentTime(0);
    tip.userPaused = false;
    tip.setPlaying(true);
  });
  return tip;
});
const observer = new IntersectionObserver(entries => {
  for (const entry of entries) {
    const tip = tips.find(tip => tip.stage === entry.target);
    tip.visible = entry.isIntersecting;
    tip.setPlaying(tip.visible && !document.hidden && !tip.userPaused && !reducedMotion.matches && tip.svg.getCurrentTime() < tip.duration);
  }
}, { threshold: 0.25 });
for (const tip of tips) observer.observe(tip.stage);
document.addEventListener('visibilitychange', () => {
  for (const tip of tips) tip.setPlaying(!document.hidden && tip.visible && !tip.userPaused && !reducedMotion.matches && tip.svg.getCurrentTime() < tip.duration);
});
reducedMotion.addEventListener('change', () => {
  for (const tip of tips) tip.setPlaying(!reducedMotion.matches && tip.visible && !tip.userPaused && !document.hidden && tip.svg.getCurrentTime() < tip.duration);
});
// Poll only visible playback to stop cleanly at its final frame; never loop by surprise.
setInterval(() => {
  for (const tip of tips) if (tip.playing && tip.svg.getCurrentTime() >= tip.duration) tip.setPlaying(false);
}, 250);
