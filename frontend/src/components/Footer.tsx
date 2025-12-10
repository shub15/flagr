import React from 'react';

const Footer: React.FC = () => {
    return (
        <footer className="w-full border-t border-gray-200/50 py-8 mt-auto animate-fade-up delay-500">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                <span className="font-serif-italic text-lg text-gray-400">Overrule</span>
                <div className="flex gap-6 text-xs text-gray-400 font-light">
                    <a href="#" className="hover:text-gray-800 transition-colors">
                        Security
                    </a>
                    <a href="#" className="hover:text-gray-800 transition-colors">
                        Privacy
                    </a>
                    <a href="#" className="hover:text-gray-800 transition-colors">
                        Terms
                    </a>
                    <a href="#" className="hover:text-gray-800 transition-colors">
                        Contact
                    </a>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
