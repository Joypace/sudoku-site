import {observeAnimations} from './animations.js';
const list = document.querySelector('#help-tips');
for (const details of list.querySelectorAll('details')) {
  details.addEventListener('toggle', () => {
    if (details.open) for (const other of list.querySelectorAll('details[open]')) {
      if (other !== details) other.open = false;
    }
  });
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
