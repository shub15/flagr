import React from 'react';

const FinalCTA: React.FC = () => {
    return (
        <section className="text-center pb-20 pt-10 animate-fade-up delay-500">
            <h2 className="font-serif-italic text-4xl md:text-5xl text-gray-900 mb-8">
                Try it on your next contract
            </h2>
            <button className="bg-black text-white px-8 py-3.5 rounded-full font-medium text-sm hover:bg-gray-800 hover:scale-105 transition-all duration-300 shadow-xl shadow-gray-400/20">
                <a href="/login"></a>Start free
            </button>
        </section>
    );
};

export default FinalCTA;
