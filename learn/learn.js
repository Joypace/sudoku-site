const players = [];
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
for (const [index, figure] of [...document.querySelectorAll('[data-example-animation]')].entries()) {
  const label = `example ${index + 1}`;
  const stage = figure.querySelector('.lesson-animation');
  const play = figure.querySelector('[data-play]');
  const replay = figure.querySelector('[data-replay]');
  const enlarge = figure.querySelector('[data-enlarge]');
  const slider = figure.querySelector('input[type=range]');
  const clock = figure.querySelector('.animation-time');
  const viewport = figure.querySelector('.animation-viewport');
  let svg, playing = false, end = 1, visible = false, frame;
  const stamp = n => `${Math.floor(n / 60)}:${String(Math.floor(n % 60)).padStart(2, '0')}`;
  const refresh = () => {
    if (!svg) return;
    const current = Math.min(end, svg.getCurrentTime());
    slider.value = String(current); clock.textContent = `${stamp(current)} / ${stamp(end)}`;
    if (current >= end) pause();
    if (playing) frame = requestAnimationFrame(refresh);
  };
  const pause = () => { playing = false; cancelAnimationFrame(frame); svg?.pauseAnimations(); play.textContent = 'Play'; play.setAttribute('aria-pressed', 'false'); play.setAttribute('aria-label', `Play ${label}`); };
  const start = () => {
    if (!svg || !visible || document.hidden) return;
    players.forEach(p => p.pause());
    if (svg.getCurrentTime() >= end) svg.setCurrentTime(0);
    playing = true; svg.unpauseAnimations(); play.textContent = 'Pause'; play.setAttribute('aria-pressed', 'true'); play.setAttribute('aria-label', `Pause ${label}`); refresh();
  };
  const load = () => {
    if (stage.querySelector('object')) return;
    const object = document.createElement('object'); object.type = 'image/svg+xml'; object.data = figure.dataset.exampleAnimation; object.setAttribute('aria-hidden', 'true'); object.tabIndex = -1;
    object.addEventListener('load', () => {
      const root = object.contentDocument?.documentElement;
      if (!root || typeof root.pauseAnimations !== 'function') { stage.querySelector('.loading').textContent = 'The animation could not load. The explanation and puzzle link are available below.'; return; }
      svg = root; const box = svg.viewBox.baseVal; if (box.width > 0 && box.height > 0) stage.style.aspectRatio = `${box.width}/${box.height}`; svg.pauseAnimations(); svg.setCurrentTime(0); end = Number(svg.dataset.duration);
      if (!Number.isFinite(end) || end <= 0) { stage.querySelector('.loading').textContent = 'Animation unavailable'; return; }
      slider.max = String(end); stage.classList.add('loaded'); [play,replay,slider].forEach(e => e.disabled = false); refresh();
    });
    stage.append(object);
  };
  play.addEventListener('click', () => playing ? pause() : start());
  replay.addEventListener('click', () => { if (svg) { pause(); svg.setCurrentTime(0); refresh(); start(); } });
  slider.addEventListener('input', () => { if (svg) { pause(); svg.setCurrentTime(Number(slider.value)); refresh(); } });
  enlarge.addEventListener('click', () => { const active = viewport.classList.toggle('enlarged'); enlarge.textContent = active ? 'Fit to page' : 'Enlarge'; enlarge.setAttribute('aria-pressed', String(active)); enlarge.setAttribute('aria-label', `${active ? 'Fit to page' : 'Enlarge'} ${label}`); viewport.tabIndex = active ? 0 : -1; });
  const observer = new IntersectionObserver(entries => { visible = entries[0].isIntersecting; if (visible) load(); else pause(); }, { threshold: .05 });
  observer.observe(stage); players.push({ pause });
}
document.addEventListener('visibilitychange', () => { if (document.hidden) players.forEach(p => p.pause()); });
reduce.addEventListener('change', () => { if (reduce.matches) players.forEach(p => p.pause()); });
