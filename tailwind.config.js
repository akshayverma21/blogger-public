/** @type {import('tailwindcss').Config} */
module.exports = {
  
    content: [
      './templates/**/*.{html,js}',
      './**/templates/**/*.{html,js}',
      './**/*.py',
    ],
    theme: {
      extend: {},
    },
    plugins: [],
  }