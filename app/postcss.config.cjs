const tailwindcss = require('tailwindcss');
const autoprefixer = require('autoprefixer');
const cssnano = require('cssnano');

const mode = process.env.NODE_ENV;
const dev = mode === 'development';

const config = {
  plugins: [
    tailwindcss(require('./tailwind.config.cjs')),
    autoprefixer(),
    !dev && cssnano({preset: 'default'}),
  ],
};

module.exports = config;
