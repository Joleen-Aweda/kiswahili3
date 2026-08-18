(() => {
  const index = Number(document.querySelector('meta[name="page-section-id"]')?.content);
  if (!Number.isFinite(index) || index < 1) return;
  const source = `./content/i18n/sw/video/page_${String(index).padStart(3, '0')}.mp4`;
  let panel;

  const show = () => {
    if (panel) return;
    panel = document.createElement('section');
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'Video ya lugha ya alama');
    panel.style.cssText = 'position:fixed;right:1rem;bottom:5rem;width:min(20rem,calc(100vw - 2rem));z-index:60;background:#000;border-radius:.6rem;overflow:hidden;box-shadow:0 8px 24px #0008';
    panel.innerHTML = `<button aria-label="Funga video ya lugha ya alama" style="float:right;position:absolute;right:.25rem;top:.25rem;z-index:1">×</button><video controls autoplay muted playsinline style="display:block;width:100%;max-height:45vh" src="${source}"></video>`;
    document.body.append(panel);
    panel.querySelector('button').onclick = () => { panel.remove(); panel = null; };
  };
  const button = document.createElement('button');
  button.type = 'button'; button.textContent = 'Lugha ya ishara'; button.setAttribute('aria-label', 'Lugha ya ishara');
  button.style.cssText = 'position:fixed;right:1rem;bottom:1rem;z-index:61;padding:.65rem .9rem;border-radius:.55rem;background:#146c43;color:#fff;border:0;font:inherit';
  button.onclick = show;
  const mountButton = () => document.body.append(button);
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountButton, { once: true });
  } else {
    mountButton();
  }
})();
