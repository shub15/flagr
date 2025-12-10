import React, { useEffect, useState } from 'react';

const Footer: React.FC = () => {
    const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

    useEffect(() => {
        const checkHealth = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/health');
                setIsHealthy(response.ok);
            } catch {
                setIsHealthy(false);
            }
        };

        checkHealth();
    }, []);

    return (
        <footer className="w-full border-t border-gray-200/50 py-8 mt-auto animate-fade-up delay-500">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                <span className="font-serif-italic text-lg text-gray-400">Overide</span>
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 px-3 py-2 rounded-full backdrop-blur-md bg-white/40 border border-white/50 shadow-sm">
                        <span
                            className={`h-2.5 w-2.5 rounded-full ${
                                isHealthy === null
                                    ? 'bg-gray-400'
                                    : isHealthy
                                    ? 'bg-emerald-500'
                                    : 'bg-rose-500'
                            } animate-pulse`}
                        />
                        <span className="text-xs font-medium text-gray-600">
                            {isHealthy === null ? 'Checking health...' : isHealthy ? 'System Online' : 'System Offline'}
                        </span>
                    </div>
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
            </div>
        </footer>
    );
};

export default Footer;
