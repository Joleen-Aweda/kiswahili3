(() => {
  try {
    localStorage.setItem('signLanguageMode', 'false');
  } catch {
    // The reader still works when storage is unavailable.
  }

  const readerIndex = Number(document.querySelector('meta[name="page-section-id"]')?.content);
  if (!Number.isFinite(readerIndex) || readerIndex < 1) return;

  // The newly inserted front cover has no sign-language video. Keep every
  // existing page paired with the same video it used before the cover was
  // added: reader page 2 uses page_001.mp4, page 3 uses page_002.mp4, etc.
  const hasSignVideo = document.querySelector('meta[name="sign-video-index"]')?.content !== 'none';
  const videoIndex = hasSignVideo ? readerIndex - 1 : 0;
  const source = videoIndex > 0
    ? `./content/i18n/sw/video/page_${String(videoIndex).padStart(3, '0')}.mp4`
    : null;
  let panel;
  let activeTrigger;

  const isSignLanguageTrigger = (button) => {
    if (!(button instanceof HTMLButtonElement)) return false;
    const label = button.getAttribute('aria-label')?.trim().toLowerCase();
    return button.hasAttribute('data-dock-trigger') &&
      (label === 'lugha ya ishara' || label === 'sign language');
  };

  const close = () => {
    panel?.remove();
    panel = null;
    activeTrigger?.setAttribute('aria-pressed', 'false');
    activeTrigger = null;
  };

  const show = (trigger) => {
    if (!source) return;
    if (panel) {
      close();
      return;
    }
    activeTrigger = trigger;
    activeTrigger.setAttribute('aria-pressed', 'true');
    panel = document.createElement('section');
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'Video ya lugha ya alama');
    panel.style.cssText = 'position:fixed;right:1rem;bottom:5rem;width:min(20rem,calc(100vw - 2rem));z-index:60;background:#000;border-radius:.6rem;overflow:hidden;box-shadow:0 8px 24px #0008';
    panel.innerHTML = `<button aria-label="Funga video ya lugha ya alama" style="float:right;position:absolute;right:.25rem;top:.25rem;z-index:1">×</button><video controls autoplay muted playsinline style="display:block;width:100%;max-height:45vh" src="${source}"></video>`;
    document.body.append(panel);
    panel.querySelector('button').onclick = close;
  };

  // Reuse the reader's built-in sign-language dock button, but keep its video
  // independent from the read-aloud mode so both can play simultaneously.
  window.addEventListener('click', (event) => {
    const trigger = event.target instanceof Element
      ? event.target.closest('button')
      : null;
    if (!isSignLanguageTrigger(trigger)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    show(trigger);
  }, true);

  window.addEventListener('pagehide', close, { once: true });
})();
