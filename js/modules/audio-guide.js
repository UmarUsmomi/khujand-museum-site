const CACHE = 'museum-audio-v1';
export function initAudioGuide() {
  const audio = document.querySelector('#guideAudio, #audioGuide') || window.museumGuideAudio;
  if (!audio) return;
  const title = document.querySelector('#agTrackName')?.textContent || 'Echo of Khujand';
  if ('mediaSession' in navigator) {
    navigator.mediaSession.metadata = new MediaMetadata({ title, artist: 'Historical Museum of Sughd Region', album: 'Эхо Худжанда' });
    navigator.mediaSession.setActionHandler('play', () => audio.play());
    navigator.mediaSession.setActionHandler('pause', () => audio.pause());
    navigator.mediaSession.setActionHandler('seekbackward', () => { audio.currentTime = Math.max(0, audio.currentTime - 10); });
    navigator.mediaSession.setActionHandler('seekforward', () => { audio.currentTime = Math.min(audio.duration || Infinity, audio.currentTime + 10); });
  }
  audio.addEventListener('progress', () => document.documentElement.classList.toggle('audio-buffering', audio.readyState < 3));
  if ('caches' in window && audio.currentSrc) caches.open(CACHE).then(cache => cache.add(audio.currentSrc)).catch(() => {});
}
