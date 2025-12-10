import React from 'react';

const Navbar: React.FC = () => {
    return (
        <nav className="relative z-20 w-full flex justify-center pt-8 px-4 animate-fade-up">
            <div className="glass-panel rounded-full px-6 py-2.5 w-full max-w-[600px] flex items-center justify-between">
                <span className="text-gray-900 font-serif-italic text-xl tracking-wide ml-2">
                    Overrule
                </span>
                <div className="flex gap-4 text-xs font-medium text-gray-500">
                    <a href="#features" className="hover:text-black transition-colors">
                        Features
                    </a>
                    <a href="#security" className="hover:text-black transition-colors">
                        Security
                    </a>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
