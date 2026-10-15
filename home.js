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
