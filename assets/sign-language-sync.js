(() => {
  const nativePlay = HTMLMediaElement.prototype.play;
  const nativePause = HTMLMediaElement.prototype.pause;
  const activeReaderAudio = new Set();

  const signVideos = () => Array.from(document.querySelectorAll(
    'video[src*="/content/i18n/"][src*="/video/"]'
  ));

  const prepareVideo = (video) => {
    video.muted = true;
    video.defaultMuted = true;
    video.volume = 0;
    video.setAttribute('aria-label', 'Video ya lugha ya alama');
  };

  const resumeSignVideo = () => {
    if (activeReaderAudio.size === 0) return;
    for (const video of signVideos()) {
      prepareVideo(video);
      const audio = activeReaderAudio.values().next().value;
      if (audio && Number.isFinite(audio.playbackRate)) {
        video.playbackRate = audio.playbackRate;
      }
      nativePlay.call(video).catch(() => {});
    }
  };

  // The reader initializes its own TTS state immediately after audio starts.
  // Retrying briefly lets the signer continue alongside it without preventing
  // the learner from using the video controls independently.
  const scheduleSignVideoResume = () => {
    [0, 150, 450].forEach((delay) => window.setTimeout(resumeSignVideo, delay));
  };

  const stopAudio = (audio) => {
    activeReaderAudio.delete(audio);
  };

  HTMLMediaElement.prototype.play = function (...args) {
    const result = nativePlay.apply(this, args);
    if (this instanceof HTMLAudioElement) {
      activeReaderAudio.add(this);
      this.addEventListener('ended', () => stopAudio(this), { once: true });
      this.addEventListener('error', () => stopAudio(this), { once: true });
      Promise.resolve(result).then(scheduleSignVideoResume).catch(() => {});
    }
    return result;
  };

  HTMLMediaElement.prototype.pause = function (...args) {
    if (this instanceof HTMLAudioElement) stopAudio(this);
    return nativePause.apply(this, args);
  };

  const observer = new MutationObserver(() => {
    for (const video of signVideos()) prepareVideo(video);
    scheduleSignVideoResume();
  });

  observer.observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener('pagehide', () => observer.disconnect(), { once: true });
})();
