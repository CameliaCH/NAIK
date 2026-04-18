let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let manualLanguage = null;
const LANG_LOCALE = { 'en': 'en-US', 'ms': 'ms-MY', 'zh': 'zh-CN' };

// Preferred voices by language — Mac enhanced voices sound much more natural
const PREFERRED_VOICES = {
  'en': ['Samantha', 'Karen', 'Daniel', 'Moira', 'Tessa'],
  'ms': ['Amira', 'Damayanti'],
  'zh': ['Tingting', 'Meijia', 'Sinji'],
};

// ── UI STATE ──
function setStatus(state, msg) {
  const statusText = document.getElementById('status-text');
  const micBtn    = document.getElementById('mic-btn');
  const micHint   = document.getElementById('mic-hint');
  const dot       = document.getElementById('status-dot');

  const i = window.i18n || {};
  const messages = {
    'idle':       i['interview.statusIdle']       || 'Ready — tap the mic to answer',
    'recording':  i['interview.statusRecording']  || 'Recording… tap to stop',
    'processing': i['interview.statusProcessing'] || 'Transcribing your answer…',
    'thinking':   i['interview.statusThinking']   || 'AI is thinking…',
    'speaking':   i['interview.statusSpeaking']   || 'AI is speaking…',
    'error':      (msg || 'Something went wrong'),
    'starting':   i['interview.statusStarting']   || 'Starting your interview…',
  };
  if (statusText) statusText.textContent = messages[state] || state;

  // Dot colour: red while recording/error, teal otherwise
  if (dot) {
    dot.style.background = (state === 'recording') ? 'var(--red)' :
                           (state === 'error')     ? '#c00' : 'var(--teal)';
    dot.classList.toggle('active', state !== 'idle');
  }

  if (micBtn) {
    const i = window.i18n || {};
    if (state === 'recording') {
      micBtn.textContent = '⏹️';
      micBtn.classList.add('recording');
      micBtn.disabled = false;
      if (micHint) micHint.textContent = i['interview.micHintRecording'] || 'Tap to stop';
    } else if (state === 'idle') {
      micBtn.textContent = '🎙️';
      micBtn.classList.remove('recording');
      micBtn.disabled = false;
      if (micHint) micHint.textContent = i['interview.micHintIdle'] || 'Click to speak';
    } else {
      micBtn.disabled = true;
      micBtn.classList.remove('recording');
      if (micHint) micHint.textContent = '';
    }
  }
}

function addToTranscript(role, text) {
  const log = document.getElementById('transcript-log');
  if (!log) return;
  const div = document.createElement('div');
  div.className = role === 'user' ? 'msg-user' : 'msg-ai';
  const i = window.i18n || {};
  const prefix = role === 'user'
    ? (i['interview.you']         || '🧑 You: ')
    : (i['interview.interviewer'] || '🤖 Interviewer: ');
  div.textContent = prefix + text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

function setManualLanguage(val) {
  manualLanguage = val === 'auto' ? null : val;
}

// ── RECORDING ──
function toggleRecording() {
  if (isRecording) stopRecording();
  else startRecording();
}

async function startRecording() {
  try {
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/mp4';
    const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, sampleRate: 16000 } });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream, { mimeType });
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(tr => tr.stop());
      const blobType = mimeType.includes('mp4') ? 'audio/mp4' : 'audio/webm';
      const blob = new Blob(audioChunks, { type: blobType });
      await handleAudio(blob);
    };
    mediaRecorder.start(250);
    isRecording = true;
    setStatus('recording');
  } catch (err) {
    const i = window.i18n || {};
    setStatus('error', i['interview.micDenied'] || 'Microphone access denied. Please allow mic access.');
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    if (audioChunks.length === 0) {
      const i = window.i18n || {};
      setStatus('error', i['interview.tooShort'] || 'Recording too short — hold the button a bit longer');
      mediaRecorder.stop();
      isRecording = false;
      return;
    }
    isRecording = false;
    mediaRecorder.stop();
    setStatus('processing');
  }
}

// ── AUDIO PIPELINE ──
async function handleAudio(blob) {
  const formData = new FormData();
  const filename = blob.type.includes('mp4') ? 'recording.mp4' : 'recording.webm';
  formData.append('audio', blob, filename);
  const sttRes = await fetch('/interview/transcribe', { method: 'POST', body: formData });
  const sttData = await sttRes.json();
  if (sttData.error) { setStatus('error', sttData.error); return; }
  addToTranscript('user', sttData.text);
  const lang = manualLanguage || sttData.language;
  setStatus('thinking');
  await getAIResponse(sttData.text, lang);
}

async function getAIResponse(text, lang) {
  const res = await fetch('/interview/respond', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language: lang })
  });
  const data = await res.json();
  if (data.error) { setStatus('error', data.error); return; }
  addToTranscript('ai', data.response);
  speakResponse(data.response, data.language);
  getAvatarVideo(data.response);
}

// ── AVATAR ──
async function getAvatarVideo(text) {
  try {
    const res = await fetch('/interview/avatar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    if (data.error) { console.warn('Avatar:', data.error); return; }
    const video = document.getElementById('avatar-video');
    const placeholder = document.getElementById('avatar-placeholder');
    if (video && placeholder) {
      video.src = data.video_url;
      video.style.display = 'block';
      placeholder.style.display = 'none';
      video.play();
    }
  } catch (err) {
    console.warn('Avatar failed (non-fatal):', err);
  }
}

// ── TEXT TO SPEECH ──
function getBestVoice(lang) {
  const voices = window.speechSynthesis.getVoices();
  const preferred = PREFERRED_VOICES[lang] || PREFERRED_VOICES['en'];

  // Try preferred voices by name first (these sound much more natural on Mac)
  for (const name of preferred) {
    const found = voices.find(v => v.name.includes(name));
    if (found) return found;
  }

  // Fall back to locale match
  const locale = LANG_LOCALE[lang] || 'en-US';
  return voices.find(v => v.lang === locale)
      || voices.find(v => v.lang.startsWith(locale.split('-')[0]))
      || null;
}

function speakResponse(text, lang) {
  window.speechSynthesis.cancel();

  // Disable mic while AI is speaking so it can't pick up its own voice
  const micBtn = document.getElementById('mic-btn');
  if (micBtn) micBtn.disabled = true;

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = LANG_LOCALE[lang] || 'en-US';
  utterance.rate = 0.9;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;

  const voice = getBestVoice(lang);
  if (voice) utterance.voice = voice;

  utterance.onstart = () => {
    setStatus('speaking');
    // Chrome bug fix: keep synthesis alive every 10 seconds
    window._ttsKeepAlive = setInterval(() => {
      window.speechSynthesis.pause();
      window.speechSynthesis.resume();
    }, 10000);
  };

  utterance.onend = () => {
    clearInterval(window._ttsKeepAlive);
    // Short delay before re-enabling mic so it doesn't catch the tail end of speech
    setTimeout(() => {
      if (micBtn) micBtn.disabled = false;
      setStatus('idle');
    }, 500);
  };

  utterance.onerror = () => {
    clearInterval(window._ttsKeepAlive);
    if (micBtn) micBtn.disabled = false;
    setStatus('idle');
  };

  window.speechSynthesis.speak(utterance);
}

// ── INTERVIEW CONTROL ──
async function beginInterview() {
  document.getElementById('start-screen').style.display = 'none';
  document.getElementById('interview-active').style.display = 'block';
  document.getElementById('stop-btn').style.display = '';
  document.getElementById('reset-btn').style.display = '';
  await startInterview();
}

function stopInterview() {
  window.speechSynthesis.cancel();
  if (isRecording) stopRecording();
  const micBtn = document.getElementById('mic-btn');
  if (micBtn) micBtn.disabled = true;
  setStatus('idle', '');
  const _i = window.i18n || {};
  document.getElementById('status-text').textContent = _i['interview.statusStopped'] || '⏹️ Interview stopped';
  document.getElementById('interview-active').style.display = 'none';
  document.getElementById('start-screen').style.display = 'block';
  document.getElementById('stop-btn').style.display = 'none';
  document.getElementById('reset-btn').style.display = 'none';
}

const OPENING_PROMPT = {
  'en': 'Please start the interview in English.',
  'ms': 'Sila mulakan temuduga dalam Bahasa Melayu.',
  'zh': '请用普通话开始面试。',
};

async function startInterview() {
  setStatus('starting');
  await fetch('/interview/reset', { method: 'POST' });
  const lang = manualLanguage || 'en';
  const openingText = OPENING_PROMPT[lang] || OPENING_PROMPT['en'];
  const res = await fetch('/interview/respond', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: openingText, language: lang })
  });
  const data = await res.json();
  if (data.error) { setStatus('error', data.error); return; }
  addToTranscript('ai', data.response);
  speakResponse(data.response, lang);
  getAvatarVideo(data.response);
}

async function resetInterview() {
  window.speechSynthesis.cancel();
  document.getElementById('transcript-log').innerHTML = '';
  const video = document.getElementById('avatar-video');
  const placeholder = document.getElementById('avatar-placeholder');
  if (video) { video.src = ''; video.style.display = 'none'; }
  if (placeholder) placeholder.style.display = 'flex';
  await startInterview();
}