import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';

function Login() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [name, setName] = useState('');
    const [email, setEmail] = useState(searchParams.get('email') || '');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        console.log('Login submitted:', { name, email, password });
        navigate('/dashboard');
    };

    return (
        <div className="min-h-screen relative overflow-hidden flex flex-col items-center justify-center p-4">
            {/* Background Elements */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-[#dcedf0] via-[#eef6f6] to-[#d8f0e9]"></div>
                <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-purple-100/30 rounded-full mix-blend-multiply filter blur-[100px] animate-pulse"></div>
                <div className="absolute bottom-[10%] right-[-5%] w-[600px] h-[600px] bg-teal-100/40 rounded-full mix-blend-multiply filter blur-[100px]"></div>
            </div>

            {/* Navigation (Minimal Logo) */}
            <nav className="absolute top-8 z-20">
                <a href="/" className="text-black font-serif-italic text-2xl tracking-wide flex items-center gap-2">
                    Overrule
                </a>
            </nav>

            {/* Sign In Card */}
            <main className="relative z-10 w-full max-w-[420px] animate-fade-up">
                <div className="glass-panel rounded-[32px] p-8 md:p-10">

                    {/* Header */}
                    <div className="text-center mb-8">
                        <h1 className="font-serif text-3xl text-black mb-2">Welcome back</h1>
                        <p className="text-sm text-gray-500 font-light">Access your personal legal council</p>
                    </div>

                    {/* Form */}
                    <form className="space-y-5" onSubmit={handleSubmit}>

                        {/* Name */}
                        <div className="space-y-1.5">
                            <label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider ml-1">
                                What should we call you?
                            </label>
                            <div className="relative group">
                                <input
                                    type="text"
                                    placeholder="Jane Doe"
                                    className="premium-input w-full rounded-xl py-3 pl-4 pr-4 text-sm text-black placeholder-gray-400"
                                    required
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Email */}
                        <div className="space-y-1.5">
                            <label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider ml-1">
                                Email address
                            </label>
                            <div className="relative group">
                                <Mail className="absolute left-4 top-3.5 w-4 h-4 text-gray-400 group-focus-within:text-black transition-colors" />
                                <input
                                    type="email"
                                    placeholder="name@company.com"
                                    className="premium-input w-full rounded-xl py-3 pl-11 pr-4 text-sm text-black placeholder-gray-400"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Password */}
                        <div className="space-y-1.5">
                            <div className="flex justify-between items-center ml-1">
                                <label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                                    Password
                                </label>
                                <a href="#" className="text-[11px] text-gray-500 hover:text-black transition-colors font-medium">
                                    Forgot?
                                </a>
                            </div>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-3.5 w-4 h-4 text-gray-400 group-focus-within:text-black transition-colors" />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    placeholder="••••••••"
                                    className="premium-input w-full rounded-xl py-3 pl-11 pr-10 text-sm text-black placeholder-gray-400"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                />
                                <button
                                    type="button"
                                    className="absolute right-4 top-3.5 text-gray-400 hover:text-black transition-colors"
                                    onClick={() => setShowPassword(!showPassword)}
                                >
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>

                        {/* Sign In Button */}
                        <button
                            type="submit"
                            className="w-full bg-black text-white py-3.5 rounded-xl font-medium text-sm mt-2 hover:bg-gray-800 hover:scale-[1.02] transition-all duration-300 shadow-[0_10px_20px_-10px_rgba(0,0,0,0.2)] flex items-center justify-center gap-2"
                        >
                            Sign In
                        </button>
                    </form>

                    {/* Divider */}
                    <div className="relative my-8">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-gray-200"></div>
                        </div>
                        <div className="relative flex justify-center text-[10px] uppercase tracking-widest">
                            <span className="bg-[#fcfbf9]/80 px-2 text-gray-400">Or continue with</span>
                        </div>
                    </div>

                    {/* Social Login */}
                    <button className="w-full bg-white border border-gray-200 text-gray-700 py-3 rounded-xl font-medium text-sm hover:bg-gray-50 hover:border-gray-300 transition-all flex items-center justify-center gap-3">
                        <img src="https://www.svgrepo.com/show/475656/google-color.svg" className="w-4 h-4" alt="Google" />
                        Google
                    </button>

                    <div className="text-center mt-8">
                        <p className="text-xs text-gray-500 font-light">
                            Don't have an account?{' '}
                            <a href="#" className="text-black font-medium hover:underline underline-offset-4 decoration-gray-300">
                                Start free
                            </a>
                        </p>
                    </div>
                </div>
            </main>

            <div className="absolute bottom-6 text-[10px] text-gray-400 font-light uppercase tracking-widest">
                Secure • Encrypted • Private
            </div>
        </div>
    );
}

export default Login;
