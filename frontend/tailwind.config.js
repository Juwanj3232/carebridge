/** @type {import('tailwindcss').Config} */
// Palette: red on white (light) and red on black (dark). The `dark` class on <html> switches themes (see index.html).
// Neutrals are `neutral` greys; red is the brand; rose (alerts), amber (nurse check) and emerald (approved) keep their meaning.
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: { extend: { fontFamily: { sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'] } } },
  plugins: [],
};
