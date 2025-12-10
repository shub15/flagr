import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Scale } from 'lucide-react';

const Hero: React.FC = () => {
    const [email, setEmail] = useState('');
    const navigate = useNavigate();

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (email) {
            navigate(`/login?email=${encodeURIComponent(email)}`);
        }
    };

    return (
        <section className="flex flex-col items-center justify-center text-center pt-20 pb-24 md:pt-32 md:pb-32">
            {/* Badge */}
            <div className="animate-fade-up delay-100 mb-8">
                <div className="glass-panel inline-flex items-center gap-2 rounded-full px-4 py-1.5">
                    <Scale className="w-3.5 h-3.5 text-gray-600" />
                    <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                        AI Document Assistant
                    </span>
                </div>
            </div>

            {/* Headline */}
            <h1 className="animate-fade-up delay-200 text-5xl md:text-7xl lg:text-[5.5rem] leading-[1.05] text-gray-900 mb-8 tracking-tight">
                <span className="block font-normal">Contract reviews you</span>
                <span className="block font-serif-italic font-normal text-gray-800 mt-2">
                    can trust instantly
                </span>
            </h1>

            {/* Subtext */}
            <p className="animate-fade-up delay-300 text-lg md:text-xl text-gray-500 font-light max-w-xl mb-10 leading-relaxed">
                Upload an agreement or policy and get clause‑level risks, suggested redlines, and
                citations. Multi‑LLM council, one clear answer.
            </p>

            {/* CTA Form */}
            <div className="animate-fade-up delay-300 w-full max-w-[480px]">
                <form
                    onSubmit={handleSubmit}
                    className="glass-panel p-1.5 rounded-2xl flex items-center shadow-lg shadow-gray-200/50"
                >
                    <input
                        type="email"
                        placeholder="Enter your email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="flex-1 bg-transparent border-none outline-none px-4 py-3 text-gray-800 placeholder-gray-400 text-base"
                    />
                    <button
                        type="submit"
                        className="bg-black text-white px-6 py-3 rounded-xl font-medium text-sm hover:bg-gray-800 hover:scale-[1.02] transition-all duration-200 whitespace-nowrap"
                    >
                        <a href="/login">Start free</a>
                    </button>
                </form>
                <div className="flex justify-between items-center mt-4 px-2">
                    <p className="text-xs text-gray-400 font-light">
                        Private by default.
                    </p>
                    <a
                        href="#"
                        className="text-xs text-gray-500 hover:text-black underline decoration-gray-300 underline-offset-4 font-light"
                    >
                        Try a sample
                    </a>
                </div>
                <p className="text-[10px] text-gray-300 mt-8 text-center uppercase tracking-widest">
                    Not Legal Advice
                </p>
            </div>
        </section>
    );
};

export default Hero;
