(() => {
  const chapters = {
    pg007_sec001: { label: 'pg007_n0010', prompt: 'pg007_n0012' },
    pg017_sec001: { label: 'pg017_n0011', prompt: 'pg017_n0012' },
    pg022_sec001: { label: 'pg022_n0012', prompt: 'pg022_n0013' },
    pg027_sec001: { label: 'pg027_n0012', prompt: 'pg027_n0014' },
    pg037_sec001: { label: 'pg037_n0014', prompt: 'pg037_n0015' },
    pg048_sec001: { label: 'pg048_n0012', prompt: 'pg048_n0015' },
    pg058_sec001: { label: 'pg058_n0010', prompt: 'pg058_n0013' },
    pg063_sec001: { label: 'pg063_n0012', prompt: 'pg063_n0013' },
    pg070_sec001: { label: 'pg070_n0012', prompt: 'pg070_n0013' },
    pg076_sec001: { label: 'pg076_n0011', prompt: 'pg076_n0012' },
    pg081_sec001: { label: 'pg081_n0011', prompt: 'pg081_n0012' },
    pg085_sec001: { label: 'pg085_n0013', prompt: 'pg085_n0014' }
  };

  const section = document.querySelector('section[data-section-id]');
  const config = section && chapters[section.dataset.sectionId];
  if (!config || section.querySelector('.book-fikiri-block')) return;

  const label = section.querySelector(`[data-id="${config.label}"]`);
  const promptText = section.querySelector(`[data-id="${config.prompt}"]`);
  if (!label || !promptText) return;

  let prompt = promptText;
  while (prompt !== section && !/pink|rose/.test(prompt.className || '')) {
    prompt = prompt.parentElement;
  }

  if (section.dataset.sectionId === 'pg022_sec001') {
    prompt = label.parentElement.parentElement;
  }

  const formerAncestors = [];
  for (let node = label.parentElement; node && node !== section; node = node.parentElement) {
    formerAncestors.push(node);
  }

  const stylesheet = document.createElement('link');
  stylesheet.rel = 'stylesheet';
  stylesheet.href = './assets/fikiri-book-style.css';
  document.head.appendChild(stylesheet);

  const block = document.createElement('div');
  block.className = 'book-fikiri-block';
  const heading = document.createElement('div');
  heading.className = 'book-fikiri-heading';
  const icon = document.createElement('img');
  icon.className = 'book-fikiri-icon';
  icon.src = './images/pg027_im003_crop_v1_crop1.png';
  icon.alt = '';
  icon.setAttribute('role', 'presentation');
  icon.setAttribute('aria-hidden', 'true');

  prompt.parentElement.insertBefore(block, prompt);
  heading.append(icon, label);
  block.append(heading, prompt);
  prompt.classList.add('book-fikiri-prompt');

  for (const node of formerAncestors) {
    if (!node.isConnected || node === prompt || node.contains(block)) continue;
    const meaningful = node.textContent.trim() || node.querySelector('[data-id], img:not([aria-hidden="true"])');
    if (!meaningful) node.remove();
  }

  const removeDecoration = (node) => {
    if (!node || node.contains(block)) return;
    const meaningful = node.textContent.trim() || node.querySelector('[data-id], img:not([aria-hidden="true"])');
    if (!meaningful) node.remove();
  };
  for (let node = block.parentElement; node && node !== section; node = node.parentElement) {
    removeDecoration(node.previousElementSibling);
    removeDecoration(node.nextElementSibling);
  }
})();
