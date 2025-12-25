import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Bell,
    ChevronDown,
    Search,
    CloudUpload,
    ShieldCheck,
    FileText,
    Building2,
    FileCheck
} from 'lucide-react';

const Knowledge = () => {
    // Shared state for toggle switches (mocked for UI purposes)
    const [toggles, setToggles] = useState<Record<string, boolean>>({
        'cal-labor': true,
        'nda-template': true,
        'gdpr': false,
        'saas-msa': true,
        'remote-policy': true,
        'sales-agreement': false,
        'vendor-code': true,
        'old-employment': false,
    });

    const handleToggle = (id: string) => {
        setToggles(prev => ({ ...prev, [id]: !prev[id] }));
    };

    return (
        <div className="min-h-screen flex flex-col">
            {/* Background Gradients (Same as Dashboard) */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] bg-rose-50/60 rounded-full blur-[100px]"></div>
                <div className="absolute bottom-[0%] left-[-10%] w-[500px] h-[500px] bg-gray-100/50 rounded-full blur-[100px]"></div>
            </div>

            {/* Header Bar (Same as Dashboard) */}
            <header className="fixed top-0 w-full z-50 glass-nav h-[60px] flex items-center justify-between px-6">
                {/* Brand */}
                <div className="flex items-center gap-2">
                    <span className="font-serif-italic text-xl tracking-wide">Overide</span>
                </div>

                {/* Center Tabs */}
                <div className="hidden md:flex gap-8 text-sm font-medium">
                    <Link to="/dashboard" className="text-gray-400 hover:text-black transition-colors pb-5 mt-5">Dashboard</Link>
                    <Link to="/knowledge" className="text-black border-b border-black pb-5 mt-5">Library</Link>
                    <a href="#" className="text-gray-400 hover:text-black transition-colors pb-5 mt-5">Settings</a>
                </div>

                {/* User Menu */}
                <div className="flex items-center gap-4">
                    <button className="relative">
                        <Bell className="w-5 h-5 text-gray-400 hover:text-black transition-colors" />
                        <span className="absolute top-0 right-0 w-2 h-2 bg-rose-500 rounded-full border-2 border-[#FDFBF7]"></span>
                    </button>
                    <div className="flex items-center gap-2 cursor-pointer pl-4 border-l border-gray-200">
                        <div className="w-8 h-8 rounded-full bg-gray-200 overflow-hidden grayscale">
                            <img src="https://i.pravatar.cc/100?img=33" alt="User" />
                        </div>
                        <ChevronDown className="w-3 h-3 text-gray-400" />
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="relative z-10 flex-1 w-full max-w-[1200px] mx-auto pt-24 pb-12 px-6">

                {/* Header Section */}
                <header className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
                    <div>
                        <h1 className="font-serif text-4xl text-black mb-2 tracking-tight">Knowledge Base</h1>
                        <p className="text-gray-500">Select the documents your AI agent should use for context.</p>
                    </div>
                    <div className="relative w-full md:w-[300px]">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search clauses, policies..."
                            className="w-full bg-white rounded-full py-3 pl-10 pr-4 text-sm shadow-sm border border-gray-100 focus:outline-none focus:border-gray-300 transition-all"
                        />
                    </div>
                </header>

                {/* Upload Section */}
                <section className="mb-8">
                    <div className="w-full bg-white/50 border-[1.5px] border-dashed border-gray-300 rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer hover:bg-white/80 hover:border-green-800 hover:shadow-sm transition-all group">
                        <div className="flex items-center gap-5">
                            <div className="w-12 h-12 bg-black rounded-full flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform">
                                <CloudUpload className="w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="font-sans font-semibold text-gray-900 mb-1">Upload New Knowledge</h3>
                                <p className="text-sm text-gray-500">Drag & drop PDF or DOCX files here, or <span className="text-green-800 underline font-medium">browse files</span></p>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Grid Layout */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

                    {/* SECTION 1: SYSTEM INTELLIGENCE */}
                    <section className="glass-panel rounded-2xl p-6 bg-white/60 backdrop-blur-md border border-white shadow-sm">
                        <div className="flex justify-between items-center mb-6">
                            <div className="flex items-center gap-3">
                                <div className="w-9 h-9 rounded-lg bg-[#e0f2f1] text-[#145336] flex items-center justify-center">
                                    <ShieldCheck className="w-5 h-5" />
                                </div>
                                <div>
                                    <h2 className="font-serif text-xl font-semibold text-black">System Standards</h2>
                                    <p className="text-xs text-gray-500">Overide's legal baselines</p>
                                </div>
                            </div>
                            <span className="bg-gray-100 px-2 py-1 rounded text-[11px] font-semibold text-gray-500">4 Active</span>
                        </div>

                        <div className="flex flex-col gap-3">
                            {/* Doc Item */}
                            <DocCard
                                icon={<FileText className="w-5 h-5" />}
                                title="California Labor Laws 2024"
                                meta="Updated 2 days ago • System"
                                active={toggles['cal-labor']}
                                onToggle={() => handleToggle('cal-labor')}
                            />
                            <DocCard
                                icon={<FileText className="w-5 h-5" />}
                                title="Standard NDA Template"
                                meta="Updated 1 week ago • System"
                                active={toggles['nda-template']}
                                onToggle={() => handleToggle('nda-template')}
                            />
                            <DocCard
                                icon={<FileText className="w-5 h-5" />}
                                title="GDPR Compliance Clause"
                                meta="Updated 1 month ago • System"
                                active={toggles['gdpr']}
                                onToggle={() => handleToggle('gdpr')}
                            />
                            <DocCard
                                icon={<FileText className="w-5 h-5" />}
                                title="SaaS MSA Framework"
                                meta="Updated 3 months ago • System"
                                active={toggles['saas-msa']}
                                onToggle={() => handleToggle('saas-msa')}
                            />
                        </div>
                    </section>

                    {/* SECTION 2: USER UPLOADS */}
                    <section className="glass-panel rounded-2xl p-6 bg-white/60 backdrop-blur-md border border-white shadow-sm">
                        <div className="flex justify-between items-center mb-6">
                            <div className="flex items-center gap-3">
                                <div className="w-9 h-9 rounded-lg bg-gray-100 text-black flex items-center justify-center">
                                    <Building2 className="w-5 h-5" />
                                </div>
                                <div>
                                    <h2 className="font-serif text-xl font-semibold text-black">Organization Uploads</h2>
                                    <p className="text-xs text-gray-500">Your internal playbooks</p>
                                </div>
                            </div>
                            <span className="bg-gray-100 px-2 py-1 rounded text-[11px] font-semibold text-gray-500">2 Active</span>
                        </div>

                        <div className="flex flex-col gap-3">
                            {/* User Doc Item */}
                            <DocCard
                                icon={<FileCheck className="w-5 h-5" />}
                                title="Internal Remote Work Policy"
                                meta="Uploaded 5 hours ago"
                                isUser={true}
                                active={toggles['remote-policy']}
                                onToggle={() => handleToggle('remote-policy')}
                            />
                            <DocCard
                                icon={<FileCheck className="w-5 h-5" />}
                                title="Q3 Sales Agreement_Final"
                                meta="Uploaded yesterday"
                                isUser={true}
                                active={toggles['sales-agreement']}
                                onToggle={() => handleToggle('sales-agreement')}
                            />
                            <DocCard
                                icon={<FileCheck className="w-5 h-5" />}
                                title="Vendor Code of Conduct"
                                meta="Uploaded 2 weeks ago"
                                isUser={true}
                                active={toggles['vendor-code']}
                                onToggle={() => handleToggle('vendor-code')}
                            />
                            <DocCard
                                icon={<FileCheck className="w-5 h-5" />}
                                title="Old_Employment_v1.docx"
                                meta="Uploaded 1 year ago"
                                isUser={true}
                                active={toggles['old-employment']}
                                onToggle={() => handleToggle('old-employment')}
                            />
                        </div>
                    </section>

                </div>
            </main>
        </div>
    );
};

// Helper Component for Document Card
const DocCard = ({ icon, title, meta, isUser = false, active, onToggle }: any) => {
    return (
        <div className="bg-white p-4 rounded-xl border border-gray-50 shadow-[0_2px_8px_rgba(0,0,0,0.02)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)] transition-shadow flex items-center gap-4">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg ${isUser ? 'bg-[#f0fdf4] text-[#166534]' : 'bg-slate-50 text-slate-600'}`}>
                {icon}
            </div>
            <div className="flex-1">
                <h3 className="text-sm font-semibold text-gray-900 mb-0.5">{title}</h3>
                <span className="text-[11px] text-gray-500 flex items-center gap-1.5">{meta}</span>
            </div>

            {/* Toggle Switch */}
            <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" checked={active} onChange={onToggle} />
                <div className="w-10 h-6 bg-gray-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-4 peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[3px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-[18px] after:transition-all peer-checked:bg-[#145336]"></div>
            </label>
        </div>
    );
};

export default Knowledge;
