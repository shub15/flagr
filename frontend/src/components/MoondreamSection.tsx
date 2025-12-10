import React from 'react';
import { ArrowRight } from 'lucide-react';

const MoondreamSection: React.FC = () => {
    return (
        <section className="w-full pb-24 animate-fade-up delay-200">
            <div className="max-w-5xl mx-auto">
                {/* Part 1: Video Left, Text Right */}
                <div className="glass-panel rounded-[40px] p-8 md:p-12 mb-12">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
                        {/* LHS Video Placeholder */}
                        <div className="aspect-video bg-black/5 rounded-2xl flex items-center justify-center border border-black/5 overflow-hidden relative group">
                            <div className="absolute inset-0 bg-gradient-to-tr from-gray-100 to-gray-50 opacity-50"></div>
                            <video className="relative z-10 w-full h-full object-cover" autoPlay loop muted playsInline>
                                <source src="/deep.mp4" type="video/mp4" />
                                Your browser does not support the video tag.
                            </video>
                        </div>

                        {/* RHS Text */}
                        <div>
                            <h2 className="font-georgia text-3xl md:text-4xl font-normal mb-6 leading-tight">
                                Normal large context LLMs <br />
                                <span className="text-gray-400">cannot understand images.</span>
                            </h2>
                            <p className="text-gray-600 font-light text-lg leading-relaxed">
                                Traditional models struggle to parse visual data accurately alongside text, leading to hallucinations or missing context entirely when dealing with complex documents.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Part 2: Text Left, Video Right */}
                <div className="glass-panel rounded-[40px] p-8 md:p-12">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
                        {/* LHS Text */}
                        <div className="order-2 md:order-1">
                            <h2 className="font-georgia text-3xl md:text-4xl font-normal mb-6 leading-tight">
                                But we can do it.
                            </h2>
                            <p className="text-gray-600 font-light text-lg leading-relaxed mb-8">
                                With advanced vision capabilities, we extract structured data from any scan or image with pixel-perfect accuracy.
                            </p>
                            <div className="flex items-center gap-3 mb-6">
                                <span className="text-sm font-medium uppercase tracking-wider text-gray-500">Powered by</span>
                                <div className="h-8 text-white rounded-full flex items-center justify-center font-bold text-sm">
                                    <img src="/md.png" alt="" className='h-12 w-auto' />
                                </div>
                            </div>


                            <a href="/login" className="group flex items-center gap-2 text-black font-medium hover:opacity-70 transition-opacity">
                                Try it yourself <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                            </a>
                        </div>

                        {/* RHS Video Placeholder */}
                        <div className="order-1 md:order-2 aspect-video bg-black rounded-2xl flex items-center justify-center border border-black/5 overflow-hidden relative shadow-2xl shadow-purple-200/50">
                            <div className="absolute inset-0 bg-gradient-to-tr from-gray-900 to-gray-800"></div>
                            {/* Decorative glow */}
                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-purple-500/30 rounded-full blur-2xl animate-pulse"></div>
                            <video className="relative z-10 w-full h-full object-cover" autoPlay loop muted playsInline>
                                <source src="/moon.mp4" type="video/mp4" />
                                Your browser does not support the video tag.
                            </video>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default MoondreamSection;
