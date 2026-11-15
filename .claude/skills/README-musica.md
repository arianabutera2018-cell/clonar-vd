# Skills de produção musical (gratuitas)

| Skill | Origem | Licença |
|---|---|---|
| audio-to-midi, midi-synth | github.com/maystudios/claude-skills | MIT |
| code-to-music, music-generation | github.com/cam10001110101/claude-skills-base | (exemplos de skills Anthropic) |
| ableton-* (12 skills) | github.com/glincker/ableton-skills | MIT |

Dependências (Python 3.13):
    apt-get install -y fluidsynth fluid-soundfont-gm sox ffmpeg
    pip install --break-system-packages music21 midi2audio pydub mido numpy scipy librosa soundfile pretty_midi pyloudnorm matchering demucs onnxruntime resampy mir_eval
    pip install --break-system-packages --no-deps basic-pitch   # usa o modelo ONNX
