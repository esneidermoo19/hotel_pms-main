document.addEventListener('DOMContentLoaded', () => {
    const root = document.documentElement;
    
    const speedSlider = document.getElementById('speedSlider');
    const intensitySlider = document.getElementById('intensitySlider');
    const amplitudeSlider = document.getElementById('amplitudeSlider');

    if (speedSlider) {
        speedSlider.addEventListener('input', (e) => {
            root.style.setProperty('--anim-speed-multiplier', e.target.value);
        });
    }

    if (intensitySlider) {
        intensitySlider.addEventListener('input', (e) => {
            root.style.setProperty('--anim-intensity', e.target.value);
        });
    }

    if (amplitudeSlider) {
        amplitudeSlider.addEventListener('input', (e) => {
            root.style.setProperty('--anim-amplitude', e.target.value + 'px');
        });
    }
});
