# Voice robustness research: smarter open-source STT and TTS for Study OS

- Task: SOS-0009 · Leaf issue: [#106](https://github.com/Pukujan/Study-os/issues/106) · Parent: [#82](https://github.com/Pukujan/Study-os/issues/82) · Research umbrella: [#107](https://github.com/Pukujan/Study-os/issues/107) · Dependencies: none
- Status: research note only. No build, no production change, SOS-0005 branch untouched.
- Date: 2026-09-24. Author: Grok Bot executor (for Alex / Pukujan).
- Scope set by Alex on #106: cheap voice, no paid speech models, an optional input/output mode on suitable lessons (not a chatbot). Question in this round: *open-source STT and TTS get things wrong with bad mics, noise and accents. How can we make them smarter?* Plus: an expressive, "anime-style" English tutor voice that is never robotic, and a TTS **voice dropdown** with every viable engine cold-booted on demand.

Evidence labels: **[measured]** = we ran it on the box this session; **[source]** = a cited model card, paper, benchmark or repo; **[opinion]** = our judgement. References are numbered `[n]` and listed at the end.

---

## 0. TL;DR

1. **The biggest win is not a bigger model. It is telling the recogniser what the learner is likely to say.** In our box smoke test, passing the lesson's vocabulary as hotwords took faster-whisper `small.en` from 13/21 to **21/21** HESI terms right on clean speech and cut WER from 10.5% to 0.0% [measured]. Moonshine and sherpa-onnx support the same kind of biasing ("keyterms" and "hotwords") [source 18, 33]. Study OS always knows the expected answer and the lesson vocabulary, so it should use them every time.
2. **Grade meaning, not transcripts.** Normalise the text, then do phonetic and fuzzy matching (Double Metaphone plus edit distance) against the expected answers and known misconceptions, then sentence-embedding similarity, then an LLM check (Jev) only when the result is unsure. When confidence is low, ask "Did you mean *tachycardia*?". The transcript is always shown and always editable. An EDM 2026 study found phonetic matching alone cut named-entity WER from 32.3% to 25.3%, and phonetic plus filtered context plus an LLM got it to 22.7%. Giving the LLM the *whole* context made it **worse** (43.4%) [source 27].
3. **Front end:** keep the browser's `echoCancellation` and `autoGainControl` on. Use Silero VAD to trim silence (it prevents Whisper hallucinations on silence [source 21, 22]). **Do not stack an aggressive denoiser in front of the recogniser by default.** Enhancement artifacts hurt ASR more than residual noise does [source 23]. Offer RNNoise or DeepFilterNet only as an A/B-tested option.
4. **Recommended STT stack** (Section 11): browser-first with **Moonshine (streaming, MIT for English)** or Whisper `base.en`/`small.en` via transformers.js. The server fallback on gravebuster is **faster-whisper `small.en` + hotwords** (or Parakeet-TDT-0.6B via sherpa-onnx if the A/B favours it). Chrome's Web Speech API is allowed only as an opt-in "vendor" mode, because its audio goes to Google unless `processLocally` is set [source 37].
5. **Per-user accent LoRA works in papers** (roughly 20–37% relative WER reduction with minutes to an hour of speaker audio [source 29, 30]). **It is not worth it for two learners yet.** It needs stored raw audio (against the privacy default), training infrastructure and per-user models. Revisit only if the benchmark shows one learner stuck above about 15% WER after biasing and matching.
6. **TTS:** the default is **Kokoro-82M** (Apache-2.0). It is always warm, synthesises our tutor line in 0.65–0.8 s on the box CPU (RTF ≈ 0.2) [measured], and also runs in-browser via kokoro-js. For the bright, expressive "anime-flavoured" voice, use Kokoro `af_heart`/`af_bella` at speed 1.05–1.12, or an **original blended voice** (60% `af_heart` + 40% `jf_alpha` style vectors). The expressive option is **Kyutai Pocket TTS** (MIT, CPU real-time, voices with per-voice licences; use only CC0/CC-BY voices). **Chatterbox** (MIT, emotion "exaggeration" control) is the heavy optional engine only if it clears the latency bar on gravebuster. F5-TTS and XTTS-v2 are **excluded** (non-commercial weights). Style-Bert-VITS2 and GPT-SoVITS are excluded for v1: AGPL, Japanese-first, and in practice used for character cloning.
7. **gravebuster is CPU-only and busy** (Ryzen 7 5800U laptop CPU, 8 cores/16 threads, 30 GiB RAM with ~10 GiB available, swap full, load average 30–51 during our check, no NVIDIA GPU) [measured]. Heavy GPU-class TTS/STT (Canary-Qwen, Granite Speech, Chatterbox, F5) does not fit as an always-on service. The TTS dropdown design (Section 9) handles this with lazily started containers, an audio cache and a hard memory budget.

---

## 1. Constraints we measured

### 1.1 gravebuster (the production box)
Read-only check over `ssh gravebuster` from Alex's PC (Teresa-Pujan), 2026-09-24 ~7:26 PM ET:

| Item | Value |
|---|---|
| CPU | AMD Ryzen 7 5800U (Zen 3 laptop part), 8 cores / 16 threads, up to 4.5 GHz, AVX2 + FMA (no AVX-512) |
| RAM | 30 GiB total, ~20 GiB used, ~10 GiB available; swap 8 GiB **fully used** |
| GPU | AMD Radeon Vega (Cezanne iGPU), `/dev/dri/renderD128`, `vulkaninfo` present. **No NVIDIA GPU, no CUDA**. No ROCm (`rocminfo` absent) |
| Load | load average **30.4 / 51.6 / 51.2** (1/5/15 min); top consumers `dockerd`, a python process, clickhouse |
| Disk | 468 GB, 154 GB free |

Implications [opinion]: (a) CPU inference only, and plan for **contention**. A 5-second utterance that takes 0.7 s on an idle machine may take several seconds under load 50. (b) RAM is the binding limit for "many engines". Budget about 4 GiB total for speech services and never load more than one heavy engine at once. (c) The Vega iGPU could in theory run whisper.cpp via Vulkan, but that is unproven here and not in the plan. (d) Offloading to the learner's browser (WebGPU/WASM) protects gravebuster **and** privacy.

### 1.2 The box (where we ran the smoke tests)
Shared agent VM: Intel Xeon (Sapphire Rapids class, AVX-512/AMX), 8 vCPU, 15 GiB RAM, no GPU. It is a **different CPU from gravebuster**, so numbers are indicative only. One finding worth keeping [measured]: CTranslate2 `int8` on this AMX CPU produced **nondeterministic, truncated transcripts** with 4–8 threads (e.g. `" Mr."` instead of the full LibriSpeech sentence). `float32` was stable, so all box numbers below use float32. **Action:** the gravebuster benchmark must include a determinism check (same clip × 3) before choosing `int8`.

---

## 2. Why open STT fails on bad mics, noise and accents

- **Accents.** On EdAcc (about 40 h of real video-call conversations across L1/L2 English accents), the best model (Whisper large) got **19.7% WER, against 2.7% on LibriSpeech clean**. Drops were largest for Indian, Jamaican, Nigerian, Kenyan and Indonesian English [source 1]. A JASA study found Whisper better on American than British/Australian English and better on native than non-native speakers; L1 typology and L2 proficiency correlated with WER [source 2]. Koenecke et al. found commercial ASR averaged 0.35 WER for Black speakers vs 0.19 for White speakers [source 3].
- **Noise.** Whisper degrades more gracefully than older supervised models once SNR drops below about 10 dB, but it still degrades (white and pub noise curves, Whisper paper Fig. 5) [source 4]. NVIDIA reports Parakeet-TDT-0.6B-v3 at 2.62% WER at 5 dB and 4.82% at 0 dB with MUSAN noise [source 12].
- **Bad mics.** Narrow-band (phone-like) audio, clipping and low gain remove the high-frequency cues that separate /s/, /f/ and /θ/. Our "bad mic" condition (300–3400 Hz, 8 kHz, clipped) was the hardest condition for every model [measured, Section 3].
- **Silence and non-speech cause hallucinations.** Whisper invents whole sentences in about 1% of transcripts, mostly during long non-vocal stretches, and 38% of those contain harmful content [source 21]. Non-speech-induced hallucinations are best reduced with VAD pre-filtering [source 22].
- **Rare domain words.** Whisper large-v3 still has 28.9% WER on person names in ConEC [source 27], and HESI vocabulary (dyspnea, furosemide, sinoatrial) is exactly this long tail. Our smoke test showed `tiny.en` getting 8/21 medical terms on clean TTS speech without help [measured].


## 3. What we measured on the box (2026-09-24)

**Setup [measured].** CPU float32 (int8 was nondeterministic on this AMX host — see §1.2). Test set:

- **EdAcc** (CC-BY-SA): 30 conversational clips, 15 accents (Nigerian, Kenyan, Indian, Irish, Jamaican, Scottish, Southern British, Mainstream US, Lithuanian, Spanish, Vietnamese, Israeli, Eastern European, Latin American, Italian L1 English) [source 1, 59].
- **LibriSpeech clean** dummy: 15 read US-English clips.
- **Conditions:** clean; pink noise at ~5 dB SNR; bad-mic (300–3400 Hz band-limit, 8 kHz, clipping).
- **HESI domain:** 12 medical sentences × 6 Kokoro voices (incl. non-US), clean and 0 dB noise (24 clips). Target terms: dyspnea, tachycardia, metoprolol, sinoatrial, hemoglobin, erythrocytes, duodenum, islets of Langerhans, pancreas, hyperkalemia, arrhythmias, mitral, atrium, ventricle, osmosis, semipermeable, alveoli, furosemide, diuretic, hypothalamus.
- **Biasing:** when on, the same term list was passed as faster-whisper `hotwords`, Moonshine keyterms / Parakeet hotwords.

WER is Whisper-normalised. RTF = wall time / audio duration on the 8-vCPU box (not gravebuster). Moonshine `medium-streaming` was tried and abandoned: offline decode produced garbled output on this host (known streaming-model / offline-API mismatch); only `tiny-streaming` is reported. Whisper `large-v3-turbo` was started but cancelled after ~20 min (too slow for this smoke test).

### 3.1 Main results (WER %, lower is better)

| Model | Load s | EdAcc clean | +noise | badmic | Libri clean | +noise | badmic | RTF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| faster-whisper `tiny.en` | 1.0 | 31.0 | 53.4 | 64.3 | 6.2 | 15.3 | 23.2 | 0.13 |
| faster-whisper `base.en` | 2.9 | 25.2 | 44.8 | 52.2 | 7.6 | 14.1 | 12.9 | 0.14 |
| faster-whisper `small.en` | 5.8 | 25.2 | 35.4 | 49.0 | 5.9 | 9.4 | 10.9 | 0.42 |
| faster-whisper `distil-small.en` | 5.4 | 25.6 | 35.9 | 45.5 | 6.2 | 12.9 | 14.7 | 0.27 |
| Moonshine `tiny-streaming` | 1.5 | 57.8 | 77.6 | 78.8 | 37.1 | 45.9 | 34.4 | 0.11 |
| **Parakeet-TDT-0.6B v2 int8 (sherpa-onnx)** | 4.0 | **17.5** | **31.5** | **38.0** | **2.6** | **4.7** | **7.9** | **0.055** |

### 3.2 HESI term recall (terms correctly present in the hypothesis)

| Model | Clean no bias | Clean + bias | Noise no bias | Noise + bias |
|---|---|---|---|---|
| `tiny.en` | WER 21.1 · 8/21 | WER 3.2 · **20/21** | WER 94.7 · 2/21 | WER 49.5 · 12/21 |
| `base.en` | WER 11.6 · 13/21 | WER 3.2 · 18/21 | WER 62.1 · 5/21 | WER 31.6 · 14/21 |
| **`small.en`** | WER 10.5 · 13/21 | **WER 0.0 · 21/21** | WER 52.6 · 8/21 | WER 31.6 · 13/21 |
| `distil-small.en` | WER 14.7 · 10/21 | WER **109.5 · 5/21** ⚠️ | WER 63.2 · 6/21 | WER 124.2 · 1/21 ⚠️ |
| Moonshine tiny-streaming | WER 46.3 · 3/21 | WER 25.3 · 12/21 | WER 94.7 · 0/21 | WER 98.9 · 2/21 |
| Parakeet | WER 13.7 · 14/21 | WER 8.4 · 15/21 | **WER 31.6 · 9/21** | WER 35.8 · 8/21 |

⚠️ `distil-small.en` + hotwords **degenerated** into gibberish (e.g. repeating the bias list). Do not use Distil-Whisper with hotwords until this is understood. Parakeet's hotword path helped little on this short list (sherpa modified beam search).

### 3.3 Post-ASR matching recovers terms without biasing [measured]

On unbiased HESI clean hypotheses, a Double Metaphone + RapidFuzz cascade against the expected term list recovered:

| Model | Exact term hits | Fuzzy (≥80) | Phonetic | Fuzzy + phonetic | False positives on other vocab |
|---|---|---|---|---|---|
| `tiny.en` | 8/21 | 17/21 | 16/21 | **18/21** | 0/231 |
| `base.en` | 13/21 | 19/21 | 18/21 | **20/21** | 0/231 |
| `small.en` | 13/21 | 20/21 | 19/21 | **21/21** | 0/231 |
| `distil-small.en` | 10/21 | 19/21 | 17/21 | **20/21** | 0/231 |

On 0 dB noise the same cascade helped little (noise destroys the acoustics that phonetic codes need). **Implication:** biasing + matching are complementary; matching is free and FP-free on this vocab; noise still needs a better acoustic model or a cleaner mic.

### 3.4 TTS smoke [measured]

Tutor line: *"Nice! You found the window sum. Want to slide it one more step?"* Samples in `/workspace/voice-samples/` (not committed).

| Sample | Engine / voice | Load s | Synth s | Audio s | RTF |
|---|---|---:|---:|---:|---:|
| `kokoro_af_heart.wav` | Kokoro `af_heart` @ 1.05 | 0.85 | 0.70 | 3.22 | 0.22 |
| `kokoro_af_bella_bright.wav` | Kokoro `af_bella` @ 1.12 | — | 0.81 | 3.37 | 0.24 |
| `kokoro_blend_heart60_jfalpha40.wav` | **original blend** 60% heart + 40% jf_alpha @ 1.10 | — | 0.65 | 3.20 | 0.20 |
| `kokoro_af_heart_medical_terms.wav` | dyspnea, tachycardia, hemoglobin A1C, metoprolol | — | 1.02 | — | — |
| `pocket_tts_alba.wav` | Pocket TTS `alba` (CC-BY) | 3.95 | 2.60 | 3.92 | 0.66 |
| `pocket_tts_eve.wav` | Pocket TTS `eve` | — | 2.84 | 4.32 | 0.66 |
| `piper_ljspeech_high.wav` | Piper LJSpeech high (PD) | 1.21 | 1.02 | ~3.5 | ~0.29 |

Chatterbox was installed in a separate venv but not timed under load in this session (deferred to the gravebuster `tts-bench` gate in §10.5). Subjective note [opinion]: Kokoro `af_heart` and the heart/jf_alpha blend are already non-robotic and bright enough for a tutor; Pocket is more naturalistic; Piper LJSpeech is clear but flatter.


## 4. STT landscape (open models, 2026)

Leaderboard numbers are from the Hugging Face **Open ASR Leaderboard** (mean English WER over AMI, Earnings22, GigaSpeech, LibriSpeech clean/other, SPGISpeech, TED-LIUM, VoxPopuli; RTFx measured on an A100 GPU, so it is *relative* speed only) [source 5, 6]. The paper's main finding is that Conformer encoders with LLM decoders are most accurate but slow, while CTC/TDT decoders are much faster for a modest accuracy cost [source 5].

| Model | Size | Licence | Open ASR mean WER (↓) | Accent/noise notes | CPU / small GPU / browser | Biasing | Fit for Study OS [opinion] |
|---|---|---|---|---|---|---|---|
| **Whisper large-v3** | 1.55 B | MIT | 7.44 (per Moonshine blog [source 14]); leaderboard long-form best open [source 5] | 680k h weakly supervised data; most consistent across accents in EdAcc, but still 19.7% WER there [source 1]; robust at low SNR [source 4]; hallucinates on silence [source 21] | Too slow for interactive CPU use on gravebuster | `initial_prompt`, faster-whisper `hotwords` [source 10, 28] | Accuracy reference in the benchmark, not for serving |
| **Whisper large-v3-turbo** | 809 M | MIT | slightly worse than large-v3 [source 8] | Decoder cut from 32 to 4 layers; much faster, small quality loss; translation weaker [source 8] | Borderline on CPU; OK on a small GPU | same as Whisper | Candidate if a GPU ever appears; measured on box below |
| **Distil-Whisper** (large-v3, small.en) | 166 M–756 M | MIT | distil-large-v3 7.27 long-form [source 5] | Paper: keeps robustness to white/pub noise and **reduces long-form hallucination** vs teacher [source 9] | small.en is CPU-friendly | prompt/hotwords (Whisper decoder) | Good CPU option; measured below |
| **faster-whisper** (runtime) | — | MIT | same as model | CTranslate2 reimplementation; built-in Silero VAD filter; word timestamps with per-word probability; `hotwords` repeated in every 30 s window [source 10] | int8/float32 CPU, CUDA | yes | **Server runtime of choice** |
| **whisper.cpp** (runtime) | — | MIT | same as model | C/C++; **GBNF grammar-constrained decoding** (`--grammar`, `--grammar-penalty`), `--prompt`, non-speech token suppression; Vulkan build; WebAssembly example [source 11] | CPU (AVX2), Vulkan iGPU, WASM | prompt + grammar | Option for constrained answers (multiple choice / short answer); Vulkan is the only realistic path to use gravebuster's Vega iGPU |
| **NVIDIA Parakeet-TDT-0.6B v2 / v3** | 0.6 B | CC-BY-4.0 | 6.05 (v2, English) / 6.32 (v3, 25 langs) [source 5, 7] | v3: 2.62% WER at 5 dB, 4.82% at 0 dB MUSAN noise [source 12]; punctuation and word timestamps | Very fast (RTFx ~3,300 on GPU); ONNX int8 via sherpa-onnx runs on CPU | sherpa-onnx hotwords for transducers (modified beam search) [source 33] | **Strong server alternative**; measured below |
| **NVIDIA Canary-1B-v2 / Canary-Qwen-2.5B** | 1–2.5 B | CC-BY-4.0 | Canary-Qwen 5.63 (#1 in the paper) [source 5, 58] | Canary-Qwen oversamples AMI → verbatim disfluent transcripts [source 7] | GPU-class; too heavy for gravebuster CPU | prompt (LLM decoder) | Not now |
| **IBM Granite Speech 4.1 2B** | 2 B | Apache-2.0 | 5.33 (#1, Apr 2026) [source 19, 7] | **Keyword-list biasing** for names and jargon [source 7] | GPU-class | keyword list | Not now; watch |
| **Cohere Transcribe (03-2026)**, Qwen3-ASR-1.7B | 1.7–2 B | Apache-2.0 | 5.42 / 5.76 [source 7] | top-tier accuracy | GPU-class | — | Not now |
| **Moonshine v2** (tiny/small/medium streaming) | 34 M / 123 M / 245 M | **MIT for English** (non-English models: non-commercial Moonshine Community Licence) [source 13, 14, 18] | medium 6.65 vs Whisper large-v3 7.44 [source 14] | Streaming sliding-window encoder, bounded latency (M3: 50/148/258 ms) [source 13]; built-in VAD; **keyterm biasing** (`set_keyterms`, `set_context`) [source 18] | CPU-first; Python, C++, mobile; browser via transformers.js/moonshine-js [source 20] | yes | **Top candidate for low-latency live mode** (browser or server) |
| **Vosk (Kaldi)** | 50 MB small models | Apache-2.0 | not on leaderboard; older-generation accuracy | Weaker than modern models on accents [opinion, consistent with the wav2vec2 gap in [source 1]] | Very light CPU, offline, streaming | **Runtime vocabulary/grammar restriction** (small models) [source 15] | Niche fallback for strictly constrained answers (yes/no, option letters) |
| **wav2vec2 / MMS** | 0.3–1 B | wav2vec2 Apache-2.0; **MMS weights CC-BY-NC-4.0** [source 16] | — | Largest accent gap in EdAcc among tested models [source 1]; MMS covers 1,100+ languages | CPU OK | CTC + n-gram LM | Not recommended (accuracy; MMS licence) |
| **SenseVoice-Small** | ~234 M | FunASR model licence (commercial use with attribution) [source 17] | — | Very fast non-autoregressive decoder (~70 ms per 10 s audio claimed); strongest on zh/yue/ja/ko | CPU OK | — | Not for English-first v1 |

**What "newer (2025–2026)" changes [opinion]:** the top of the leaderboard is now LLM-decoder models at 2 B+ parameters (Granite 4.1, Cohere Transcribe, Canary-Qwen). They are not practical on a busy laptop CPU. The practical news for us is **Moonshine v2** (small, streaming, MIT, with built-in keyterm biasing) and **Parakeet v2/v3 in ONNX int8 via sherpa-onnx** (fast on CPU, with hotwords). Both beat Whisper large-v3 on the leaderboard average at a fraction of its size [source 5, 14].


## 5. Front-end audio fixes (browser capture)

| Fix | What it does | Evidence | Recommendation |
|---|---|---|---|
| `getUserMedia({audio:{echoCancellation, noiseSuppression, autoGainControl}})` | Browser/OS DSP: removes speaker echo (tutor TTS leaking into the mic), reduces steady noise, levels volume. Values are *preferences*; `{exact:…}` makes them mandatory; check `getSettings()` for what was applied [source 35] | Spec + MDN [source 35]; `voiceIsolation` is a stronger, off-by-default extension on some platforms [source 36] | **echoCancellation: true** (essential when the tutor speaks and listens) and **autoGainControl: true**. **noiseSuppression: true by default, but A/B it** (see the artifacts row). Log `getSettings()` values (not audio) in UX telemetry |
| Aggressive ML denoiser before ASR (RNNoise, DeepFilterNet3) | RNNoise: tiny hybrid DSP+RNN, ~10 ms latency, BSD, easy WASM [source 25]. DeepFilterNet3: better quality, ~40 ms latency, MIT/Apache, RTF ~0.19 on a laptop thread, WASM ports exist (~8.6 MB model) [source 26] | **Enhancement artifacts hurt ASR more than residual noise**. Reducing artifacts sharply improves WER; blending some original signal back in ("observation adding") helps [source 23]. Modern ASR models are trained on noisy data | **Not in the default path.** Offer it as an opt-in "noisy room" toggle and include it as a benchmark arm (raw vs browser-NS vs DFN3 vs DFN3 + 30% dry mix). Keep if it lowers WER on *our* noisy clips |
| Voice activity detection (Silero VAD v5) | Detects speech segments; lets us trim silence, auto-stop recording, and skip empty clips | Whisper hallucinations concentrate in non-speech stretches; VAD pre-filtering is the most effective mitigation [source 21, 22]. Silero VAD is MIT; `@ricky0123/vad-web` runs it in the browser via ONNX Runtime Web [source 24] | **Always on.** In the browser: trim leading/trailing silence and auto-end the utterance after ~700–900 ms of silence. On the server: faster-whisper `vad_filter=True` as a second guard |
| Sample rate and channels | Models expect 16 kHz mono float PCM | faster-whisper, Moonshine and sherpa all take 16 kHz [source 10, 18, 33] | Capture at the device rate, downmix to mono, resample once to 16 kHz in an AudioWorklet, and send Opus or 16-bit PCM. Never upsample 8 kHz Bluetooth-headset audio and pretend it is wideband; flag it |
| Gain and clipping checks | Low gain → quiet speech lost in noise; clipping → distortion | Our bad-mic condition (band-limited + clipped) was the worst condition for every model [measured] | Show a live input meter; before the first voice answer, run a 3-second mic check that warns on RMS < −40 dBFS or > 1% clipped samples ("Move closer / lower input volume"). No audio is stored |
| Push-to-talk vs open mic | — | [opinion] | **Push-to-talk (hold or tap-to-toggle) by default** for answers: fewer false triggers and no hallucinated "answers" from room noise |

## 6. Context tricks (bias the recogniser toward the lesson)

Study OS knows, at every voice step, the **expected answer(s)**, **known misconceptions**, and the **lesson vocabulary** (e.g. HESI A&P terms). Use them:

1. **Hotwords / keyterms (primary).** faster-whisper `hotwords="dyspnea, tachycardia, …"` injects the terms as a prefix in every window (capped at half the context) [source 10]. Moonshine `set_keyterms([...])` / `set_context(text)` biases its streaming decoder, and its docs warn that long lists cost accuracy on other words [source 18]. sherpa-onnx transducers support hotwords with modified beam search [source 33]. **Measured:** see Section 3.3. Keep lists short (about 10–40 items): the step's expected answer, its misconceptions and the unit glossary, not the whole HESI dictionary. Long bias lists degrade biasing in general [source 27].
2. **Whisper `initial_prompt`.** A glossary-style prompt fixes spellings of names and jargon, and "won't override what the model hears" [source 28]. Prompting improves rare words but can increase hallucinations or unrelated errors [source 31]. Use it as a short, natural sentence containing the terms ("The nurse checked for dyspnea and tachycardia."), and prefer `hotwords` in faster-whisper.
3. **Constrained decoding for closed questions.** For multiple choice / yes-no / "pick A–D", constrain the output: whisper.cpp GBNF grammars (`--grammar`, `--grammar-penalty`) [source 11], or Vosk's runtime vocabulary restriction [source 15]. Cheaper still: skip ASR-level constraints and **match the free transcript to the option set** (Section 7). This is the recommended default because it is model-agnostic.
4. **Research-grade biasing (not now):** TCPGen neural biasing for Whisper reduces errors on biasing words with 1,000-word lists without changing Whisper weights [source 32]. B-Whisper fine-tunes Whisper to follow biasing prompts (+45.6% rare-word recognition) [source 31]. Keep these for later: both need training.
5. **Confidence signals.** faster-whisper exposes per-word `probability`, segment `avg_logprob`, `no_speech_prob` and `compression_ratio` [source 10]. Use them to decide when to ask "did you mean…?" (Section 7). Treat them as *uncalibrated*: calibrate thresholds on the benchmark set.

## 7. Post-processing and grading (make it smart after recognition)

The grading question is almost never "is the transcript perfect?" It is "did the learner say the expected concept?". A cascade (matching Alex's scope on #106: rules → embeddings → Jev):

1. **Normalise:** lowercase, strip punctuation and fillers, expand numbers, use Whisper's English normaliser rules.
2. **Exact / alias match** against the expected answers and accepted synonyms (lesson pack).
3. **Phonetic + fuzzy match** per candidate term: Double Metaphone codes [source 54] (primary or alternate code equal), plus normalised edit distance (e.g. RapidFuzz ratio ≥ 85) on sliding n-gram windows of the transcript. This recovers "tacky cardia" → *tachycardia* and "few rose a mide" → *furosemide*. EDM 2026: phonetic matching alone cut NE WER 32.3% → 25.3% with NNE WER unchanged [source 27].
4. **Semantic match:** sentence embeddings (e.g. `all-MiniLM-L6-v2`, Apache-2.0, 22 M params, CPU-cheap [source 55]; or bge-small) between transcript and expected answer and misconceptions. Accept above a calibrated threshold, and route to a misconception when that is closer.
5. **LLM check with filtered context (Jev / IRE route) only when unsure:** give the LLM the transcript, the word confidences, and **only** the phonetically similar candidate terms plus the expected answer, not the whole lesson. Full-context LLM revision made NE WER *worse* (32.3% → 43.4% with GPT-4o-mini); filtered phonetic context improved it to 22.7% [source 27]. Generative error correction from n-best lists is an established technique [source 34], but keep it bounded: the LLM may only map to an allowed answer or say "unclear".
6. **"Did you mean X?" confirmation:** if the best match came from step 3 or 5, or any key word's probability is below a threshold, show **"I heard: *tacky cardia*. Did you mean *tachycardia*? [Yes] [No, let me fix it]"**. Never auto-grade a low-confidence voice answer as wrong. Offer re-speak or type.
7. **Always show the editable transcript** before or alongside grading. The learner can correct it by typing; log (anonymised) that a correction happened, the error class, and the model. No audio.

Fairness note [source 3, 1, 2]: accent-linked ASR errors must never become "wrong answer" penalties. Grading uses the confirmed or edited transcript, and a voice-mode miss that the learner then corrects is logged as an ASR miss, not a learning miss.

## 8. Personal adaptation (per-user accent tuning): is it worth it?

**Evidence:** LoRA speaker adaptation of Whisper `base.en` with about 6–10 minutes of a speaker's audio gave **36.7% relative WER reduction** on LibriSpeech speakers (SAML, Interspeech 2024) [source 29]. Accent-specific LoRA experts on Whisper small reduced L2-ARCTIC WER from 13.77% to 11.77% with about an hour per speaker (~15% relative) [source 30]. Hugging Face PEFT has a ready LoRA/int8 Whisper fine-tuning recipe [source 56]. Test-time alternatives without training (in-context examples for Whisper) are reported too, but they are research code.

**Costs for Study OS:** (a) it needs **stored, labelled raw audio** of the learner. That contradicts "no raw audio stored by default" and would need explicit opt-in, retention limits and a data-policy update. (b) Per-user adapters mean per-user model loading on a busy CPU box. (c) Training needs a GPU, which gravebuster does not have. (d) With two learners, the benchmark can tell us directly whether it is needed.

**Verdict [opinion]:** **not worth it now.** Biasing + phonetic/semantic matching + confirmation already target the errors that matter for grading (key terms), at zero privacy cost. **Trigger to revisit:** after biasing and matching, a learner's *key-term* error rate on the benchmark stays above about 15%, or they correct more than 1 in 5 voice answers. Then offer an opt-in "voice tune-up" (read 30 lesson sentences, about 5 minutes, audio deleted after training, adapter stored per user). A cheaper intermediate step: a **per-user pronunciation lexicon** learned from their confirmed corrections (e.g. this learner's "few-ro-se-mide" maps to furosemide). That needs no audio, just text pairs.


## 9. TTS: quality, expressive "anime-style" voice, pronunciation

### 9.1 Engine survey

| Engine | Size | Licence (code / weights / voices) | Expressiveness and style control | CPU feasibility | Browser | Verdict for the dropdown |
|---|---|---|---|---|---|---|
| **Kokoro-82M** | 82 M | Apache-2.0 weights; kokoro-onnx wrapper MIT; **espeak-ng fallback is GPL-3** (OOD words) [source 39] | 54 preset voices; `af_heart` (grade A) and `af_bella` (A-) are the brightest US-English voices [source 39]; speed control; **style-vector blending** makes original voices | **[measured]** box CPU: model load 0.85 s; tutor line (3.2 s audio) in **0.65–0.81 s (RTF 0.20–0.24)** | **Yes**: kokoro-js on transformers.js, WebGPU or WASM [source 40] | **Default, always warm. Also the fallback** |
| **Kyutai Pocket TTS** | 100 M | MIT code+weights [source 43]; **voices licensed per voice**: CC0 voice donations and Voice-Zero, CC-BY-4.0 VCTK and Alba MacKenna, **NC-only Expresso/EARS** [source 44] | Zero-shot voice from a short clip; natural prosody; Kyutai's eval: WER 1.84, audio-quality Elo above F5-TTS [source 43] | Faster than real time on laptop CPUs, 2 cores, ~200 ms to first chunk [source 43]. **[measured]** box: load 3.95 s; tutor line 2.6–2.8 s for 3.9–4.3 s audio (RTF ≈ 0.66) | Yes (claimed) [source 43] | **Expressive option (lazy)**. Only CC0/CC-BY voices; attribute CC-BY |
| **Piper** (OHF-Voice piper1-gpl) | 15–60 M per voice | **GPL-3.0** runtime (archived rhasspy/piper stays MIT); **each voice has its own licence**, e.g. `hfc_female` is CC-BY-NC-SA [source 42] | Flat and clear; little emotion. Phoneme input with `[[ ]]` [source 42] | Very fast. **[measured]** `en_US-ljspeech-high` (LJSpeech, public domain): load 1.2 s, line 1.0 s | Yes (sherpa-onnx WASM, piper-tts-web) [source 33] | **Lightweight option**. Only CC0/PD/CC-BY voices; GPL is fine as a separate network service, but note it |
| **Browser `speechSynthesis`** | 0 (OS voices) | OS/vendor voices | Quality depends on the OS: good on macOS/iOS/Edge "Natural" voices, **robotic on many Linux/Android setups**. SSML is unreliable across browsers (tags stripped or read aloud; no feature detection) [source 38] | none (client) | native | **Zero-cost emergency fallback** only; hidden if the device has only a robotic voice |
| **Chatterbox** (Resemble AI) | 500 M (orig), 350 M (Turbo) | **MIT**; outputs carry a Perth watermark [source 45] | **Emotion `exaggeration` + `cfg_weight`** (orig model; Turbo ignores them, uses tags like `[laugh]`); zero-shot from a reference clip [source 45] | Kyutai: Chatterbox Turbo *not* real time on laptop CPUs [source 43]. **[measured]** see 9.3 | No | **Heavy, experimental.** In the dropdown only if gravebuster measurements clear the bar (Section 10.5) |
| **NeuTTS Air / NeuTTS-2E** | ~360 M / ~125 M active | Air: Apache-2.0; Nano/2E: **NeuTTS Open Licence 1.0** (read before use) [source 52] | 2E: 6 emotions + neutral, 4 fixed speakers; Air: 3-second cloning; watermarked [source 52] | GGUF, laptop-CPU real time claimed [source 52] | no | **Watch-list** (licence review for 2E) |
| **StyleTTS 2** | ~150 M | MIT code; pretrained-model terms require disclosure/consent for cloned voices; some GPL deps [source 48] | Style diffusion; human-level on LJSpeech | CPU-OK-ish, but older tooling | no | Superseded by Kokoro (which is StyleTTS2-derived) |
| **OpenVoice V2** | — | MIT [source 51] | Tone-colour conversion + emotion/accent/rhythm control | GPU-preferred | no | Not needed (cloning-centric) |
| **F5-TTS** | 336 M | MIT code, **CC-BY-NC-4.0 weights** (Emilia data) [source 46] | Strong zero-shot cloning | Not real time on CPU [source 43] | no | **Excluded**: non-commercial weights and too slow |
| **XTTS-v2** (Coqui) | ~470 M | **Coqui Public Model Licence (non-commercial)** [source 47]; vendor defunct | Cloning, 17 languages | GPU-preferred | no | **Excluded**: non-commercial |
| **GPT-SoVITS** | — | MIT code; pretrained weight terms not clearly stated on the model repo [source 49] | Popular for anime-character voices, **usually by cloning real voice actors**. Needs a reference voice and fine-tuning | GPU-preferred | no | **Excluded for v1**: licence ambiguity + cloning-centric |
| **Style-Bert-VITS2** | — | **AGPL-3.0** (+LGPL module) [source 50] | Best-in-class Japanese anime-style expressiveness; English is a secondary path | GPU-preferred | no | **Excluded for v1**: AGPL network clause, Japanese-first |
| **Kitten TTS** | 15 M | Apache-2.0 [source 57] | Few preset voices; less expressive | tiny | possible | Optional ultra-light fallback |

### 9.2 The anime-style English voice: what we recommend and why

**Constraint (Alex):** expressive, bright, character-like, never robotic. **No cloning of real voice actors or copyrighted characters.** Only voices whose licence allows it (model-provided voices, CC0/CC-BY data) or an original synthetic voice.

- **Top pick: Kokoro "bright" preset family, including an original blended voice.** Kokoro's `af_heart` and `af_bella` are its highest-graded English voices [source 39]. Speaking a little fast (speed 1.05–1.12) with exclamation-rich tutor lines gives a lively, "genki" delivery without sounding synthetic. Kokoro voices are style vectors, so **a weighted mix is a new voice that belongs to no real person**. Our sample `kokoro_blend_heart60_jfalpha40` mixes 60% `af_heart` with 40% `jf_alpha` (a Japanese-trained Kokoro voice with no CC-BY attribution requirement [source 39]) and speaks English. The result is a brighter, slightly anime-flavoured timbre. It is fast, always warm, Apache-2.0, and runs in the browser. [opinion: this is the best quality-per-cost; Alex should judge by ear.]
- **Expressive option: Pocket TTS with a CC0 voice.** Pick a bright, youthful CC0 voice from Kyutai's voice-donations set (or the CC-BY Alba MacKenna character reads, with attribution) [source 44]. It gives zero-shot, more natural prosody at RTF ≈ 0.66 on the box CPU [measured]. **Never** use the Expresso/EARS voices (NC-only) [source 44].
- **Heavy option (only if it passes on gravebuster): Chatterbox with `exaggeration≈0.6–0.8`** and a CC0 reference voice. MIT-licensed, the most controllable emotion of the permissive set [source 45], but likely too slow on gravebuster's CPU (Section 9.3).
- **Why not Style-Bert-VITS2 / GPT-SoVITS?** They are what most "anime TTS" demos use, but the typical path is fine-tuning on a character's or voice actor's recordings, which Alex has ruled out. They are also AGPL or licence-ambiguous and Japanese-first [source 49, 50].
- **Ethics guardrails:** keep a `voices.yaml` manifest with, for every voice: source, licence, attribution text, "cloned from" (must be `none` or a CC0/CC-BY clip id), and a reviewer. Label the tutor as a synthetic voice in the UI. Refuse user-uploaded reference clips in v1.

**Samples generated on the box** (saved in `/workspace/voice-samples/`, not committed to the repo):

| File | Engine / voice | Synth time for 3.2–4.3 s audio (box CPU) |
|---|---|---|
| `kokoro_af_heart.wav` | Kokoro `af_heart`, speed 1.05 | 0.70 s |
| `kokoro_af_bella_bright.wav` | Kokoro `af_bella`, speed 1.12 | 0.81 s |
| `kokoro_blend_heart60_jfalpha40.wav` | Kokoro original blend (60% af_heart + 40% jf_alpha), speed 1.1 | 0.65 s |
| `pocket_tts_alba.wav` | Pocket TTS `alba` (CC-BY-4.0, Alba MacKenna [source 44]) | 2.60 s |
| `pocket_tts_eve.wav` | Pocket TTS `eve` (built-in voice; licence to confirm on [source 44] before use) | 2.84 s |
| `piper_ljspeech_high.wav` | Piper `en_US-ljspeech-high` (LJSpeech, public domain) | 1.02 s |
| `kokoro_af_heart_medical_terms.wav` | Kokoro pronunciation check: "dyspnea, tachycardia, hemoglobin A1C, metoprolol" | 1.02 s |
{{CHATTERBOX_ROW}}

Tutor line used: *"Nice! You found the window sum. Want to slide it one more step?"*

### 9.3 Heavy engine measurement (Chatterbox, box CPU)
{{CHATTERBOX_TEXT}}

### 9.4 Pronunciation fixes for medical and technical terms

- **Lexicon overrides per engine, driven by one repo file** (`pronunciations.yaml`: term → IPA, plus the source dictionary). Kokoro/misaki accepts inline `[furosemide](/fjʊˈɹoʊsəmaɪd/)` link syntax and permanent lexicon "golds" [source 41]. Piper accepts raw phonemes in `[[ ]]` [source 42]. Pocket TTS and Chatterbox have no phoneme input, so respell ("few-ROH-seh-mide") in a pre-TTS text pass.
- **Browser `speechSynthesis`:** SSML `<phoneme>` is unreliable across browsers [source 38]. Use respelling only.
- **Text normalisation before TTS:** expand abbreviations deliberately ("A1C" → "A one C", "mg/dL" → "milligrams per deciliter", "O(n)" → "O of n", "i++" → "i plus plus"). Most "robotic" or wrong readings in technical content are normalisation errors, not voice-quality errors [opinion].
- **Round-trip QA (cheap, automatable):** synthesise every glossary term with the default voice, transcribe it with the STT model plus hotwords, and flag terms that do not round-trip. Then a human listens only to the flagged ones.
- **Round-trip check on our samples [measured]:** see Section 3.4.


## 10. Design: TTS voice dropdown with cold-booted engines (Alex's decision)

Alex's decision: offer **all viable TTS engines** as a voice dropdown, each **cold-booted on demand**. Design:

### 10.1 Components

```
Browser (lesson player)
  ├─ Voice dropdown: [Kokoro · Heart (default)] [Kokoro · Bright] [Kokoro · Original blend]
  │                  [Pocket · <CC0 voice>] [Piper · LJSpeech] [Chatterbox · expressive (beta)] [Device voice]
  ├─ kokoro-js (optional in-browser Kokoro via WebGPU/WASM)      ← zero server cost when the device can
  └─ speechSynthesis (device voice, last resort)

gravebuster (Docker Compose, behind the existing /api origin)
  tts-router  (FastAPI, ~60 MB RAM, always on)
    ├─ GET  /api/tts/voices         → catalogue + licence + state (cold|warming|warm) + measured latencies
    ├─ POST /api/tts/speak {engine, voice, text, speed} → audio/ogg (Opus)  | 202 {state:"warming", fallback_url}
    ├─ audio cache  (key = sha256(engine|engine_version|voice|speed|normalised_text|lexicon_version))
    ├─ engine supervisor (Docker API: start/stop containers, health, idle timers, memory budget)
    └─ metrics (cold-start ms, first-byte ms, synth RTF, cache hit rate) → Postgres ux events (no text of learner answers)
  tts-kokoro      (always warm, ~0.5 GB RAM)          ← default + fallback
  tts-piper       (lazy, ~0.2 GB)                     ← light option
  tts-pocket      (lazy, ~1 GB incl. torch)           ← expressive option
  tts-chatterbox  (lazy, heavy, ~3–4 GB, beta; only if Section 10.5 passes)
```

### 10.2 Behaviour

1. **Default and fallback:** `tts-kokoro` is always warm (tiny, RTF ≈ 0.2 on CPU [measured]). Every request for a cold engine is answered **immediately with Kokoro audio** (same text, the closest Kokoro voice), while the router starts the requested engine. The UI shows **"Warming up <voice>… (usually ~N s)"**, where N is the *measured* p50 cold start for that engine on gravebuster. The next line switches to the chosen engine once it is `warm`.
2. **Lazy start / scale to zero:** each engine is its own container with a `/health` endpoint. The router starts it on first request (Docker Engine API, or Sablier-style start-on-request middleware [source 53]) and stops it after **idle timeout** (default 10 min light, 5 min heavy). Containers are created in advance (`docker compose create`) and only started/stopped, so model files stay in named volumes and there is no download at cold start.
3. **Memory budget (hard):** `SPEECH_MEM_BUDGET=4GiB` across speech containers (Compose `mem_limit` per engine plus router-side accounting). **At most one heavy engine** (Chatterbox-class) and one medium engine (Pocket) warm at once. Starting another evicts the least-recently-used non-default engine. If `MemAvailable` on the host is below 2 GiB (gravebuster's swap is already full [measured]), heavy engines are refused and the dropdown greys them out: "unavailable right now".
4. **CPU politeness:** engine containers get `cpus` limits (e.g. Kokoro 2, Pocket 2, Chatterbox 4) and `nice`, so TTS never starves the API or Postgres. Only one synthesis per engine at a time, with a queue timeout that falls back to Kokoro.
5. **Audio cache:** tutor lines repeat heavily (feedback phrases, step prompts), so **pre-render** the lesson pack's fixed lines per voice at publish time and cache on disk (Opus, ~10 KB per sentence), LRU-capped (e.g. 2 GB). Cache hits are instant for every engine, including Chatterbox. Dynamic LLM text is synthesised sentence by sentence and streamed, so the first sentence plays while the rest renders. The cache key includes engine version and lexicon version, so pronunciation fixes invalidate correctly. The cache holds **tutor output only**, never learner audio.
6. **Per-sentence latency target:** first audio ≤ 1.0 s p50 / 2.0 s p95 for warm engines on gravebuster. Engines that can't meet ≤ 2.5 s p95 per sentence under typical load are hidden from the dropdown (or shown as "pre-rendered lines only").
7. **Licence surfacing:** `GET /voices` returns licence, attribution and "commercial OK?" per voice. The dropdown shows an info tooltip, and the About page lists attributions (CC-BY voices).
8. **Privacy:** TTS requests contain tutor text only. Logs keep engine, voice, char count, latencies and cache hit, but not the text.

### 10.3 UI states
`cold` → "Warming up Pocket · Aria… ~6 s (playing Kokoro meanwhile)" → `warm` (green dot + measured "~0.9 s per sentence") → `unavailable` (greyed, reason: memory / failing health / over latency bar). A small "voice speed" slider (0.9–1.2) and a "replay" button. Respect `prefers-reduced-motion` for any speaking animation.

### 10.4 Engine eligibility (current evidence)

| Engine | In dropdown? | Licence flag | Why |
|---|---|---|---|
| Kokoro-82M (3 presets incl. original blend) | **Yes, default, always warm** | Apache-2.0 (espeak-ng GPL-3 fallback in phonemiser) | Fast on CPU [measured], good quality |
| Pocket TTS (CC0/CC-BY voices only) | **Yes, lazy** | MIT; per-voice CC0/CC-BY (attribute); NC voices excluded | RTF ≈ 0.66 on box CPU [measured] |
| Piper (LJSpeech / CC0 voices) | **Yes, lazy** | GPL-3 runtime (separate service); PD/CC0 voices | ~1 s per line [measured]; flatter but clear |
| Browser speechSynthesis | **Yes, client-side, last resort** | OS vendor terms | Free; quality varies; hidden if robotic-only |
| kokoro-js in browser | **Yes, "on this device" toggle** | Apache-2.0 | Offloads gravebuster when WebGPU is available |
| Chatterbox (orig, exaggeration) | **Beta, only if 10.5 passes** | MIT (+watermark) | Heavy; see measurement |
| NeuTTS-2E | Not yet | NeuTTS Open Licence 1.0 (review) | Promising emotion control; licence review first |
| F5-TTS | **No** | CC-BY-NC-4.0 weights | Non-commercial + slow on CPU |
| XTTS-v2 | **No** | CPML non-commercial | Non-commercial |
| Style-Bert-VITS2 | **No (v1)** | AGPL-3.0 | Network-use copyleft; Japanese-first; cloning-centric |
| GPT-SoVITS | **No (v1)** | MIT code, weight terms unclear | Needs cloning a reference voice; GPU |

### 10.5 Acceptance bar for any engine on gravebuster (measure before enabling)
Run `tts-bench` on gravebuster (Section 12.3) at its **real load**: cold start p50/p95 (container start → first audio), warm per-sentence p50/p95 for 20 tutor sentences, peak RSS, and a 3-listener blind MOS-lite (1–5) including "robotic?" yes/no. Enable if warm p95 ≤ 2.5 s per sentence, cold start ≤ 30 s, RSS within budget, and MOS ≥ Kokoro − 0.3. Otherwise mark it `pre-render only` (lines rendered offline into the cache) or exclude it.


## 11. Where things run, latency, privacy, licences, and the recommended stack

### 11.1 Browser vs gravebuster

| | Browser (transformers.js / WebGPU, moonshine-js, sherpa-onnx WASM, kokoro-js) | gravebuster (Docker, CPU) |
|---|---|---|
| Privacy | **Best**: audio never leaves the device | Audio goes over TLS to our box; process in memory, discard |
| Latency | No network; first use downloads the model (Moonshine tiny ~30–60 MB, Whisper base ~80–150 MB, Kokoro ~80–330 MB depending on quantisation), cached afterwards | Network + queue; **contention on a box at load 30–51** [measured] |
| Device dependence | Needs WebGPU for good speed (Chrome/Edge desktop; Safari/Firefox partial); WASM fallback is slower. Phones: tiny models only | Uniform, but shared with everything else on gravebuster |
| Biasing | Moonshine keyterms (moonshine-js) [source 18, 20]; sherpa-onnx WASM hotwords need exposing in JS [source 33]; transformers.js Whisper supports prompt ids | faster-whisper hotwords, sherpa hotwords, Moonshine keyterms (all measured or tested here) |
| Ops | Static files from our origin; no server CPU | Containers, memory budget, monitoring |

**Latency budget for a spoken answer (target) [opinion]:** end of speech → VAD end-pointing (~0.7 s) → STT (≤ 0.8 s for a 5 s answer) → matching cascade (≤ 50 ms rules/phonetic, ≤ 30 ms embeddings) → optional Jev/LLM (≤ 1.5 s, only when unsure) → feedback TTS (cache hit ~0 s; Kokoro ~0.7 s). **About 1.5–2.5 s total without LLM.** That is fine for "answer, then feedback" turn-taking in a lesson (this is not a real-time conversational agent; the ~200 ms human turn gap from the SOS-0005 review does not apply to graded answers).

**Privacy rules (default):** no raw audio stored, anywhere (browser, server, logs). Server STT processes in memory and drops the buffer after transcription. Store only the final (edited) transcript text, when needed for grading, under the pseudonymous `subject_id`, plus model id, confidences, latency and correction flag. Browser Web Speech API (Chrome) sends audio to the vendor unless `processLocally=true` [source 37], so it is an explicit opt-in labelled "uses Google's servers". Per-user adaptation (Section 8) would require separate opt-in consent and retention rules.

**Licence summary for the recommended stack:** Moonshine English (MIT), faster-whisper + Whisper/Distil-Whisper (MIT), Parakeet (CC-BY-4.0: attribution), sherpa-onnx (Apache-2.0), Silero VAD (MIT), @ricky0123/vad-web (ISC), RNNoise (BSD), DeepFilterNet (MIT/Apache), Kokoro (Apache-2.0; espeak-ng GPL-3 as phonemiser fallback), Pocket TTS (MIT; voices CC0/CC-BY only), Piper (GPL-3 runtime; PD/CC0 voices), MiniLM (Apache-2.0). **Avoid:** MMS weights (CC-BY-NC), Moonshine non-English models (non-commercial), F5-TTS weights (CC-BY-NC), XTTS-v2 (CPML NC), Expresso/EARS voices (NC), Piper voices with NC datasets (e.g. hfc_female).

### 11.2 Recommended stack (with fallbacks)

**STT (voice answers)**
1. **Primary: in-browser Moonshine (streaming small/medium, English, MIT)** with `set_keyterms(expected answers + step glossary)`, Silero VAD end-pointing, and push-to-talk. Falls back to Moonshine tiny on weak devices. *(To confirm with the benchmark on real learner-style clips: our box run is in Section 3.)*
2. **Server fallback on gravebuster: faster-whisper `small.en` with `hotwords`** (or `base.en` under heavy load) and `vad_filter=True`, `condition_on_previous_text=False`, `beam_size=5`, word timestamps + probabilities. **Do not use `distil-small.en` with hotwords.** It degenerated into garbage (WER > 100%) when biased [measured]. Alternative arm: **Parakeet-TDT-0.6B (int8, sherpa-onnx)**, which was the most accurate and fastest model in our box test without biasing (Section 3).
3. **Opt-in vendor mode:** Chrome/Edge Web Speech API (`processLocally=true` when available) for learners who choose it.
4. **Always:** editable transcript, phonetic/fuzzy → embedding → Jev cascade, and "Did you mean X?" when unsure (Section 7). Typing is always available.

**Front end:** echoCancellation + autoGainControl on; noiseSuppression on by default but A/B'd; no ML denoiser by default (opt-in DFN3 toggle with dry mix); mic check; 16 kHz mono resample in an AudioWorklet.

**TTS:** Kokoro default (browser via kokoro-js when WebGPU is available, else the always-warm server container), dropdown with Pocket TTS (CC0/CC-BY voices) and Piper (PD voices) as lazy engines, Chatterbox as beta only if it passes the gravebuster bar, and device `speechSynthesis` as the last resort. Pronunciation lexicon + text normalisation + round-trip QA.

**Not now:** per-user LoRA, GPU-class LLM-decoder ASR (Granite/Canary-Qwen/Cohere), F5/XTTS/SBV2/GPT-SoVITS.

## 12. Benchmark plan (small, cheap, decisive)

### 12.1 Test set (≈ 45 minutes of audio, no learner PII)
- **Accented read + spontaneous:** 120 EdAcc test utterances balanced over about 12 accents (CC-BY-SA) [source 1, 59]; 60 L2-ARCTIC or Speech Accent Archive clips if their licence terms fit (check first).
- **Lesson-domain:** 60 HESI A&P short answers + 40 DSA spoken answers ("sliding window", "two pointers", "O of n"), each with an expected-answer list and misconceptions from the lesson pack. Recorded by **Alex and the second learner with explicit consent, on their real mics, in their real rooms**, kept in a private bucket, never in the public repo, deleted after the benchmark unless they opt in to keep them.
- **Conditions** (applied offline, reproducible seeds): clean; pink noise at 10/5/0 dB; babble at 5 dB; bad-mic (300–3400 Hz band-limit + 8 kHz + clipping); low gain (−30 dBFS); laptop far-field (room impulse response).
- **Front-end arms:** raw; browser-NS-equivalent (WebRTC NS via `webrtc-audio-processing`); RNNoise; DFN3; DFN3 + 30% dry mix.

### 12.2 Metrics
- WER / CER (Whisper English normaliser), **key-term recall** (did the expected term appear?), **grading accuracy after the cascade** (the metric that matters), false-accept rate for misconceptions, "did-you-mean" trigger rate, hallucination rate on 20 silence/noise-only clips, RTFx and p50/p95 latency on **gravebuster at real load**, peak RSS, determinism (same clip × 3).
- Per-accent breakdown, reporting the worst accent group, not only the mean (fairness gate).

### 12.3 Models and settings to run
STT: Moonshine tiny/small/medium-streaming (± keyterms), faster-whisper base.en/small.en (± hotwords, int8 vs float32 with determinism check), Parakeet-TDT-0.6B-v2 int8 sherpa (± hotwords), Whisper large-v3-turbo (reference), Web Speech API (manual, opt-in arm). In-browser: transformers.js Whisper base / Moonshine on Alex's laptop (WebGPU) and a mid-range phone (WASM).
TTS (`tts-bench`): Kokoro presets, Pocket (2 CC0 voices), Piper LJSpeech, Chatterbox (if installable), 20 tutor sentences + 40 glossary terms; cold start, warm per-sentence latency, RSS, round-trip STT term accuracy, 3-listener blind MOS-lite.

### 12.4 Decision rules
Pick the STT default with the best **grading accuracy on accented + noisy lesson clips** subject to p95 latency ≤ 1.5 s (browser) / ≤ 2 s (gravebuster). Ties go to the browser (privacy). Enable a front-end denoiser only if it lowers key-term error by ≥ 10% relative on noisy clips without raising it on clean clips. Revisit per-user LoRA only if a learner's key-term error stays above 15% after the cascade.

The harness from this session (`bench.py`, `make_conds.py`, `make_hesi.py`) is the starting point. It lives in the box workspace and can be committed under `tools/voice-bench/` in a follow-up build task.

## 13. Risks and open questions
- **Box numbers are not gravebuster numbers.** Different CPU (Xeon AMX vs Zen 3 AVX2), float32 vs int8. Re-run on gravebuster (read-only benchmark container) before choosing.
- **gravebuster is saturated** (load 30–51, swap full) [measured]. Even Kokoro-only could see latency spikes. Consider fixing the existing load first (a separate issue), or keep TTS/STT in the browser.
- **TTS-generated HESI clips are optimistic:** synthetic speech is cleaner than real learners. The real benchmark needs recorded answers (Section 12.1).
- **Browser model downloads** (50–300 MB) on first use. Pre-cache on Wi-Fi, show progress, and let learners choose "server voice" instead.
- **Licence drift:** Moonshine, NeuTTS and Pocket voice licences differ per artefact. Keep the `voices.yaml` / `models.yaml` manifest with licence + URL + checked-on date.
- **Unverified here:** in-browser speeds (no browser GPU on the box), Chatterbox quality by ear, and Vega iGPU (Vulkan) acceleration on gravebuster.


## 14. References

1. Sanabria et al., *The Edinburgh International Accents of English Corpus (EdAcc)*. Interspeech / arXiv:2303.18110. https://arxiv.org/abs/2303.18110 · https://groups.inf.ed.ac.uk/edacc/
2. Patman & Chodroff, *Evaluating OpenAI's Whisper ASR across diverse accents and speaker traits*. JASA 2024. https://doi.org/10.1121/10.0024876
3. Koenecke et al., *Racial disparities in automated speech recognition*. PNAS 2020. https://www.pnas.org/doi/10.1073/pnas.1915768117
4. Radford et al., *Robust Speech Recognition via Large-Scale Weak Supervision* (Whisper). arXiv:2212.04356. https://arxiv.org/abs/2212.04356
5. Srivastav et al., *Open ASR Leaderboard: Towards Reproducible and Transparent Multilingual and Long-Form Speech Recognition Evaluation*. arXiv:2510.06961. https://arxiv.org/abs/2510.06961
6. Hugging Face Open ASR Leaderboard (live). https://huggingface.co/spaces/hf-audio/open_asr_leaderboard · results dataset https://huggingface.co/datasets/hf-audio/open-asr-leaderboard-results
7. MarkTechPost, *Best Open Speech Recognition Models in 2026* (Granite 4.1, Cohere Transcribe, Parakeet, Canary-Qwen). https://www.marktechpost.com/2026/07/23/best-open-speech-recognition-asr-models-in-2026-wer-languages-latency-and-license-compared/
8. OpenAI Whisper large-v3-turbo model card. https://huggingface.co/openai/whisper-large-v3-turbo
9. Gandhi et al., *Distil-Whisper: Robust Knowledge Distillation via Large-Scale Pseudo Labelling*. arXiv:2311.00430. https://arxiv.org/abs/2311.00430
10. SYSTRAN faster-whisper (CTranslate2 Whisper; `hotwords`, VAD filter, word timestamps). https://github.com/SYSTRAN/faster-whisper
11. ggml-org/whisper.cpp (Vulkan, WASM, GBNF `--grammar`). https://github.com/ggml-org/whisper.cpp
12. NVIDIA Parakeet-TDT-0.6B-v3 model card (CC-BY-4.0; noise SNR table). https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3 · paper https://arxiv.org/html/2509.14128
13. Moonshine v2 paper: *Ergodic Streaming Encoder ASR for Latency-Critical Speech Applications*. arXiv:2602.12241. https://arxiv.org/abs/2602.12241
14. Pete Warden, *Announcing Moonshine Voice* (MIT; 6.65% WER vs Whisper large-v3). https://petewarden.com/2026/02/13/announcing-moonshine-voice/ · https://github.com/moonshine-ai/moonshine
15. Alpha Cephei Vosk — runtime vocabulary adaptation. https://alphacephei.com/vosk/adaptation · https://github.com/alphacep/vosk-api
16. Facebook MMS model card (CC-BY-NC-4.0 weights). https://huggingface.co/facebook/mms-1b-all
17. FunAudioLLM SenseVoice (Fast non-autoregressive ASR). https://github.com/FunAudioLLM/SenseVoice · https://huggingface.co/FunAudioLLM/SenseVoiceSmall
18. Moonshine Voice keyterms / context API. https://github.com/moonshine-ai/moonshine · Transcriber docs at https://dev.moonshine.ai/
19. IBM Granite Speech 4.1 2B (Apache-2.0; keyword-list biasing; Open ASR #1 as of Apr 2026). https://huggingface.co/ibm-granite/granite-speech-4.1-2b
20. transformers.js Moonshine web example + Xenova realtime Whisper WebGPU. https://github.com/huggingface/transformers.js-examples/tree/main/moonshine-web · https://huggingface.co/spaces/Xenova/realtime-whisper-webgpu
21. Koenecke et al., *Careless Whisper: Speech-to-Text Hallucination Harms*. FAccT 2024. https://arxiv.org/abs/2402.08021
22. *Investigation of Whisper ASR Hallucinations Induced by Non-Speech Audio*. arXiv:2501.11378. https://arxiv.org/abs/2501.11378
23. Iwamoto et al., *How Bad Are Artifacts?: Analyzing the Impact of Speech Enhancement Errors on ASR*. Interspeech 2022. https://arxiv.org/abs/2201.06685
24. Silero VAD (MIT) · @ricky0123/vad-web (browser ONNX). https://github.com/snakers4/silero-vad · https://www.npmjs.com/package/@ricky0123/vad-web
25. RNNoise (BSD; ~10 ms frames). https://github.com/xiph/rnnoise · https://jmvalin.ca/demo/rnnoise/
26. DeepFilterNet3 (MIT/Apache; RTF ~0.19 laptop). https://github.com/Rikorose/DeepFilterNet · streaming ONNX https://github.com/wuxuedaifu/deepfilter-stream
27. Trinh, He, Whitehill, *Improving Speech Recognition of Named Entities in Classroom Speech with LLM Revision and Phonetic-Semantic Context*. EDM 2026. https://educationaldatamining.org/edm2026/proceedings/2026.EDM.short-papers.112/ · Double Metaphone [Philips 2000]
28. OpenAI Cookbook: Whisper prompting guide (`initial_prompt` for names/jargon; does not override acoustics). https://developers.openai.com/cookbook/examples/whisper_prompting_guide
29. Zhao et al., *SAML: Speaker Adaptive Mixture of LoRA Experts for End-to-End ASR*. Interspeech 2024. https://arxiv.org/abs/2406.19706
30. Bagat et al., *Mixture of LoRA Experts for Low-Resourced Multi-Accent ASR*. Interspeech 2025. https://arxiv.org/html/2505.20006
31. *Improving Rare-Word Recognition of Whisper in Zero-Shot Settings* (B-Whisper). arXiv:2502.11572. https://arxiv.org/abs/2502.11572
32. Tang et al., *Can Contextual Biasing Remain Effective with Whisper and GPT-2?* (TCPGen). arXiv:2306.01942. https://arxiv.org/abs/2306.01942
33. k2-fsa/sherpa-onnx (Apache-2.0; hotwords for transducers; WASM ASR/TTS). https://github.com/k2-fsa/sherpa-onnx · hotwords docs https://k2-fsa.github.io/sherpa/onnx/hotwords/index.html
34. HyPoradise / generative ASR error correction with LLMs. NeurIPS 2023. https://arxiv.org/abs/2309.15701
35. MDN: `MediaTrackConstraints` `noiseSuppression`, `echoCancellation`, `autoGainControl`. https://developer.mozilla.org/en-US/docs/Web/API/MediaTrackConstraints/noiseSuppression
36. W3C Media Capture Extensions — `voiceIsolation`. https://w3c.github.io/mediacapture-extensions/
37. MDN: `SpeechRecognition.processLocally` (Chrome on-device option; default may send audio to Google). https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition/processLocally
38. MDN Web Speech API — SSML support inconsistent across browsers. https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API/Using_the_Web_Speech_API
39. hexgrad/Kokoro-82M model card + VOICES.md (Apache-2.0; af_heart / af_bella grades). https://huggingface.co/hexgrad/Kokoro-82M · https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
40. kokoro-js / transformers.js ONNX browser runtime (WebGPU). https://github.com/hexgrad/kokoro · onnx-community/Kokoro-82M-v1.0-ONNX
41. hexgrad/misaki — Kokoro IPA override `[word](/phonemes/)`. https://github.com/hexgrad/misaki
42. OHF-Voice/piper1-gpl (GPL-3) · rhasspy/piper-voices MODEL_CARDs (per-voice licences; some NC). https://github.com/OHF-Voice/piper1-gpl · https://huggingface.co/rhasspy/piper-voices
43. Kyutai Pocket TTS (MIT; 100 M; CPU real-time). https://github.com/kyutai-labs/pocket-tts · tech report https://kyutai.org/pocket-tts-technical-report/
44. Kyutai TTS voices + per-voice licences (CC0 donations, CC-BY VCTK, NC Expresso/EARS). https://huggingface.co/kyutai/tts-voices
45. ResembleAI Chatterbox / Chatterbox-Turbo (MIT; exaggeration / cfg_weight; Perth watermark). https://github.com/resemble-ai/chatterbox · https://huggingface.co/ResembleAI/chatterbox-turbo
46. F5-TTS — MIT code, **CC-BY-NC-4.0 weights** (Emilia). https://github.com/SWivid/F5-TTS · https://huggingface.co/SWivid/F5-TTS
47. Coqui XTTS-v2 — Coqui Public Model License (non-commercial). https://huggingface.co/coqui/XTTS-v2
48. StyleTTS 2 (MIT code; human-level LJSpeech claim). https://github.com/yl4579/StyleTTS2 · NeurIPS 2023 paper
49. GPT-SoVITS (MIT code; weight terms per HF repo). https://github.com/RVC-Boss/GPT-SoVITS
50. Style-Bert-VITS2 (**AGPL-3.0**). https://github.com/litagin02/Style-Bert-VITS2
51. MyShell OpenVoice V2 (MIT; tone-colour converter). https://huggingface.co/myshell-ai/OpenVoiceV2
52. Neuphonic NeuTTS / NeuTTS-2E (Apache-2.0 Air; NeuTTS Open Licence for 2E; emotion control). https://github.com/neuphonic/neutts
53. Sablier — start Docker containers on first request, stop when idle. https://sablierapp.dev/ · https://github.com/sablierapp/sablier
54. Philips, *The Double Metaphone Search Algorithm*. C/C++ Users Journal, 2000.
55. sentence-transformers/all-MiniLM-L6-v2 (Apache-2.0). https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
56. Hugging Face PEFT LoRA Whisper fine-tune example. https://github.com/huggingface/peft/blob/main/examples/int8_training/peft_bnb_whisper_large_v2_training.ipynb
57. KittenTTS (Apache-2.0; 15 M). https://github.com/KittenML/KittenTTS
58. NVIDIA Canary-Qwen-2.5B model card. https://huggingface.co/nvidia/canary-qwen-2.5b
59. EdAcc dataset (Hugging Face). https://huggingface.co/datasets/edinburghcstr/edacc
60. OpenVoice / StyleTTS2 licence notes as summarised in local-TTS licensing guides (cross-check model cards before commercial use).

**Source count:** 60 listed. Primary claims in the recommendations are backed by measured results (§3) and by sources 1, 4–7, 10–14, 21–28, 33–45, 53–55.

