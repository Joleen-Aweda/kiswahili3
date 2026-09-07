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

  const clamp = (value, minimum, maximum) =>
    Math.min(Math.max(value, minimum), maximum);

  const makeDraggable = (container) => {
    const handle = container.querySelector('[data-sign-drag-handle]');
    let drag;

    const finishDrag = (event) => {
      if (!drag || event.pointerId !== drag.pointerId) return;
      if (handle.hasPointerCapture(event.pointerId)) {
        handle.releasePointerCapture(event.pointerId);
      }
      drag = null;
    };

    handle.addEventListener('pointerdown', (event) => {
      if (event.target.closest('button')) return;
      const rect = container.getBoundingClientRect();
      drag = {
        pointerId: event.pointerId,
        offsetX: event.clientX - rect.left,
        offsetY: event.clientY - rect.top,
      };
      container.style.left = `${rect.left}px`;
      container.style.top = `${rect.top}px`;
      container.style.right = 'auto';
      container.style.bottom = 'auto';
      handle.setPointerCapture(event.pointerId);
      event.preventDefault();
    });

    handle.addEventListener('pointermove', (event) => {
      if (!drag || event.pointerId !== drag.pointerId) return;
      const maximumX = Math.max(0, window.innerWidth - container.offsetWidth);
      const maximumY = Math.max(0, window.innerHeight - container.offsetHeight);
      container.style.left = `${clamp(event.clientX - drag.offsetX, 0, maximumX)}px`;
      container.style.top = `${clamp(event.clientY - drag.offsetY, 0, maximumY)}px`;
    });

    handle.addEventListener('pointerup', finishDrag);
    handle.addEventListener('pointercancel', finishDrag);
  };

  const show = (trigger) => {
    if (!source) return;
    if (panel) {
      close();
      return;
    }
    activeTrigger = trigger || null;
    activeTrigger?.setAttribute('aria-pressed', 'true');
    panel = document.createElement('section');
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'Video ya lugha ya alama');
    panel.style.cssText = 'position:fixed;right:1rem;bottom:5rem;width:min(20rem,calc(100vw - 2rem));z-index:60;background:#000;border-radius:.6rem;overflow:hidden;box-shadow:0 8px 24px #0008';
    panel.innerHTML = `<div data-sign-drag-handle style="display:flex;align-items:center;justify-content:flex-end;min-height:2.25rem;padding:.25rem .35rem;background:#171717;color:#fff;cursor:move;touch-action:none;user-select:none" aria-label="Kishikio cha video ya lugha ya alama"><button data-sign-close aria-label="Funga video ya lugha ya alama" style="min-width:2rem;min-height:2rem;border:0;border-radius:.35rem;background:#333;color:#fff;font-size:1.3rem;line-height:1">×</button></div><video controls autoplay muted playsinline style="display:block;width:100%;max-height:45vh" src="${source}"></video>`;
    document.body.append(panel);
    panel.querySelector('[data-sign-close]').onclick = close;
    makeDraggable(panel);
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

  const openAutomatically = () => {
    if (source && !panel) show(null);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', openAutomatically, { once: true });
  } else {
    openAutomatically();
  }

  window.addEventListener('pagehide', close, { once: true });
})();
