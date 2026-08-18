(() => {
  const nativePlay = HTMLMediaElement.prototype.play;
  const nativePause = HTMLMediaElement.prototype.pause;
  const activeReaderAudio = new Set();
  let syncingVideo = false;

  const signVideos = () => Array.from(document.querySelectorAll(
    'video[src*="/content/i18n/"][src*="/video/"]'
  ));

  const prepareVideo = (video) => {
    video.muted = true;
    video.defaultMuted = true;
    video.volume = 0;
    video.removeAttribute('autoplay');
    video.setAttribute('aria-label', 'Video ya lugha ya alama');
  };

  const syncPlayback = () => {
    const shouldPlay = activeReaderAudio.size > 0;
    for (const video of signVideos()) {
      prepareVideo(video);
      syncingVideo = true;
      if (shouldPlay) {
        const audio = activeReaderAudio.values().next().value;
        if (audio && Number.isFinite(audio.playbackRate)) {
          video.playbackRate = audio.playbackRate;
        }
        nativePlay.call(video).catch(() => {});
      } else {
        nativePause.call(video);
      }
      syncingVideo = false;
    }
  };

  const stopAudio = (audio) => {
    activeReaderAudio.delete(audio);
    window.setTimeout(syncPlayback, 120);
  };

  HTMLMediaElement.prototype.play = function (...args) {
    if (this instanceof HTMLAudioElement) {
      activeReaderAudio.add(this);
      this.addEventListener('ended', () => stopAudio(this), { once: true });
      this.addEventListener('error', () => stopAudio(this), { once: true });
      window.setTimeout(syncPlayback, 0);
    }
    return nativePlay.apply(this, args);
  };

  HTMLMediaElement.prototype.pause = function (...args) {
    if (this instanceof HTMLAudioElement) stopAudio(this);
    return nativePause.apply(this, args);
  };

  const observer = new MutationObserver(() => {
    for (const video of signVideos()) prepareVideo(video);
    syncPlayback();
  });

  observer.observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener('pagehide', () => observer.disconnect(), { once: true });
})();
