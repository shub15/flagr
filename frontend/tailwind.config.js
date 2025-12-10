/** @type {import('tailwindcss').Config} */
/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                'serif': ['Instrument Serif', 'serif'],
                'sans': ['Inter', 'sans-serif'],
                'georgia': ['Georgia', 'serif'],
            },
        },
    },
    plugins: [],
}
