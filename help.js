import {observeAnimations} from './animations.js';
const list = document.querySelector('#help-tips');
try {
  const response = await fetch('../home-assets/tips.json');
  if (!response.ok) throw Error('Catalogue unavailable');
  const catalog = await response.json();
  list.replaceChildren();
  for (const tip of catalog.tips) {
    const details = document.createElement('details');
    details.id = tip.id;
    details.setAttribute('name', 'app-tips');
    const summary = document.createElement('summary');
    summary.textContent = tip.title.en;
    const stage = document.createElement('div');
    stage.className = 'tip-animation';
    stage.dataset.tip = tip.id;
    stage.dataset.src = `../home-assets/${tip.id}.svg`;
    const placeholder = document.createElement('div');
    placeholder.className = 'tip-placeholder';
    const title = document.createElement('p');
    title.textContent = tip.title.en;
    const status = document.createElement('small');
    status.textContent = 'Loading animation…';
    placeholder.append(title, status);
    stage.append(placeholder);
    const description = document.createElement('p');
    description.className = 'help-description';
    description.textContent = tip.description;
    details.append(summary, stage, description);
    details.addEventListener('toggle', () => {
      if (details.open) for (const other of list.querySelectorAll('details[open]')) {
        if (other !== details) other.open = false;
      }
    });
    list.append(details);
  }
  observeAnimations(list);
  const openTarget = () => {
    const target = document.getElementById(location.hash.slice(1));
    if (target?.tagName === 'DETAILS') {
      target.open = true;
      target.scrollIntoView({block: 'start', behavior: 'instant'});
    }
  };
  openTarget();
  addEventListener('hashchange', openTarget);
} catch {
  list.textContent = 'The tips could not load. Please refresh the page to try again.';
}
