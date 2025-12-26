import { useState } from 'react';
import {
    ChevronLeft,
    ChevronRight,
    Bell,
    Plus,
    Download
} from 'lucide-react';

const CalendarTab = () => {
    const [view, setView] = useState<'month' | 'week'>('month');

    // Mock Data for Scatterplot
    // x: 0-100 (converted from days), y: 0-100 (risk score), r: size
    const scatterData = [
        { x: 15, y: 92, r: 25, label: "TechGuard MSA", cp: "TechGuard Inc.", val: "$1.2M", date: "Oct 24", risk: "Critical", desc: "Uncapped liability & auto-renew." },
        { x: 120, y: 85, r: 15, label: "CloudFlare DPA", cp: "CloudFlare", val: "$450k", date: "Feb 12", risk: "High", desc: "Missing key GDPR clauses." },
        { x: 45, y: 65, r: 10, label: "HubSpot Renewal", cp: "HubSpot", val: "$120k", date: "Nov 22", risk: "Medium", desc: "Price increase cap exceeding 5%." },
        { x: 200, y: 20, r: 30, label: "WeWork Lease", cp: "WeWork", val: "$2.5M", date: "May 2026", risk: "Low", desc: "Standard lease terms, compliant." },
        { x: 10, y: 45, r: 8, label: "Slack Upgrade", cp: "Slack", val: "$40k", date: "Oct 19", risk: "Medium", desc: "Review user seat allocation." },
        { x: 60, y: 88, r: 18, label: "Consulting Agmt", cp: "McKinsey", val: "$800k", date: "Dec 10", risk: "High", desc: "IP ownership ambiguity detected." },
        { x: 300, y: 15, r: 12, label: "Cleaning Svcs", cp: "CleanCo", val: "$50k", date: "Aug 2026", risk: "Low", desc: "Low value, standard terms." }
    ];

    const getRiskColor = (score: number) => {
        if (score >= 80) return { bg: 'bg-red-500', text: 'text-red-700', border: 'border-red-500' };
        if (score >= 50) return { bg: 'bg-orange-500', text: 'text-orange-700', border: 'border-orange-500' };
        return { bg: 'bg-green-600', text: 'text-green-700', border: 'border-green-600' };
    };

    return (
        <div className="animate-fade-up w-full">
            {/* Header Actions */}
            <div className="flex justify-between items-end mb-8">
                <div>
                    <h1 className="font-serif text-4xl text-black tracking-tight mb-2">Contract Control Center</h1>
                    <p className="text-gray-500">Monitor renewals, obligations, and global risk.</p>
                </div>
                <div className="flex gap-3">
                    <button className="bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-full text-sm font-medium hover:bg-gray-50 flex items-center gap-2">
                        <Bell className="w-4 h-4" /> Alerts (3)
                    </button>
                    <button className="bg-black text-white px-4 py-2 rounded-full text-sm font-medium hover:bg-gray-900 flex items-center gap-2">
                        <Plus className="w-4 h-4" /> Add Event
                    </button>
                </div>
            </div>

            {/* SECTION 1: CALENDAR */}
            <section className="bg-white/60 backdrop-blur-md border border-white/90 rounded-2xl shadow-sm p-6 mb-8">
                <div className="flex justify-between items-center mb-6">
                    <div className="flex items-center gap-4">
                        <h2 className="font-serif text-2xl text-black">December 2025</h2>
                        <div className="flex bg-gray-100 rounded-full p-1">
                            <button className="p-1 hover:bg-white rounded-full transition-all"><ChevronLeft className="w-4 h-4" /></button>
                            <button className="p-1 hover:bg-white rounded-full transition-all"><ChevronRight className="w-4 h-4" /></button>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="bg-gray-100 p-1 rounded-full flex">
                            <button
                                onClick={() => setView('month')}
                                className={`px-4 py-1.5 rounded-full text-xs font-medium transition-all ${view === 'month' ? 'bg-white shadow-sm text-black' : 'text-gray-500'}`}
                            >
                                Month
                            </button>
                            <button
                                onClick={() => setView('week')}
                                className={`px-4 py-1.5 rounded-full text-xs font-medium transition-all ${view === 'week' ? 'bg-white shadow-sm text-black' : 'text-gray-500'}`}
                            >
                                Week
                            </button>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500 font-medium">
                            <span className="w-2 h-2 rounded-full bg-red-600"></span> High Risk
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500 font-medium">
                            <span className="w-2 h-2 rounded-full bg-orange-500"></span> Medium
                        </div>
                    </div>
                </div>

                {/* Calendar Grid */}
                <div className="border border-gray-200 rounded-lg overflow-hidden bg-gray-200 gap-[1px] grid grid-cols-7">
                    {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                        <div key={day} className="bg-gray-50 p-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">
                            {day}
                        </div>
                    ))}

                    {/* Placeholder Days */}
                    {[28, 29, 30].map(d => (
                        <div key={`prev-${d}`} className="bg-white/50 min-h-[120px] p-3 text-gray-300 font-medium">{d}</div>
                    ))}

                    {/* Current Month Days */}
                    {Array.from({ length: 31 }, (_, i) => i + 1).map(day => (
                        <div key={day} className={`bg-white min-h-[120px] p-3 transition-colors hover:bg-gray-50 relative ${day === 9 ? 'bg-green-50/50' : ''}`}>
                            <span className={`text-sm font-medium block mb-2 ${day === 9 ? 'text-green-700 font-bold' : 'text-gray-500'}`}>{day}</span>

                            {day === 2 && (
                                <div className="bg-red-50 text-red-700 border-l-2 border-red-600 px-2 py-1.5 rounded text-[10px] mb-1 font-medium cursor-pointer hover:-translate-y-0.5 transition-transform">
                                    <span className="font-bold opacity-80 mr-1">Expiring</span> TechGuard
                                </div>
                            )}

                            {day === 6 && (
                                <div className="bg-orange-50 text-orange-700 border-l-2 border-orange-500 px-2 py-1.5 rounded text-[10px] mb-1 font-medium cursor-pointer hover:-translate-y-0.5 transition-transform">
                                    <span className="font-bold opacity-80 mr-1">Notice</span> Slack
                                </div>
                            )}

                            {day === 9 && (
                                <div className="bg-green-50 text-green-700 border-l-2 border-green-600 px-2 py-1.5 rounded text-[10px] mb-1 font-medium cursor-pointer hover:-translate-y-0.5 transition-transform">
                                    <span className="font-bold opacity-80 mr-1">Audit</span> GDPR Check
                                </div>
                            )}

                            {day === 13 && (
                                <>
                                    <div className="bg-red-50 text-red-700 border-l-2 border-red-600 px-2 py-1.5 rounded text-[10px] mb-1 font-medium cursor-pointer hover:-translate-y-0.5 transition-transform">
                                        <span className="font-bold opacity-80 mr-1">Auto-Renew</span> Salesforce
                                    </div>
                                    <div className="text-[10px] text-gray-400 pl-2 mt-1 font-medium">+ 2 others</div>
                                </>
                            )}
                        </div>
                    ))}
                </div>
            </section>

            {/* SECTION 2: PORTFOLIO */}
            <section>
                {/* KPI Tiles */}
                <div className="grid grid-cols-4 gap-6 mb-8">
                    {[
                        { label: 'Portfolio Value', val: '$4.2M', trend: 'Across 142 Active Docs', color: 'text-gray-500', valColor: 'text-gray-900' },
                        { label: 'Critical Priority', val: '5', trend: 'High Risk + Expiring < 30d', color: 'text-red-600', valColor: 'text-red-600' },
                        { label: 'Avg Risk Score', val: '42', trend: '↓ 3 pts from last month', color: 'text-green-600', valColor: 'text-gray-900' },
                        { label: 'Renewal Volume', val: '12', trend: 'Upcoming in Q4', color: 'text-gray-500', valColor: 'text-gray-900' }
                    ].map((kpi, i) => (
                        <div key={i} className="bg-white p-6 rounded-2xl border border-gray-100 shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
                            <div className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">{kpi.label}</div>
                            <div className={`font-serif text-3xl mb-2 ${kpi.valColor}`}>{kpi.val}</div>
                            <div className={`text-xs font-medium ${kpi.color}`}>{kpi.trend}</div>
                        </div>
                    ))}
                </div>

                {/* Chart Controls */}
                <div className="flex justify-between items-center mb-4">
                    <div className="flex gap-4">
                        <span className="text-xs font-medium flex items-center gap-1.5 text-gray-500"><span className="w-2 h-2 rounded-full bg-red-600"></span> High Risk ({'>75'})</span>
                        <span className="text-xs font-medium flex items-center gap-1.5 text-gray-500"><span className="w-2 h-2 rounded-full bg-orange-500"></span> Medium (50-75)</span>
                        <span className="text-xs font-medium flex items-center gap-1.5 text-gray-500"><span className="w-2 h-2 rounded-full bg-green-600"></span> Low ({'<50'})</span>
                    </div>
                    <div className="flex gap-2">
                        <button className="bg-black text-white px-4 py-1.5 rounded-full text-xs font-medium">View: Scatter</button>
                        <button className="bg-white border border-gray-200 text-gray-600 px-4 py-1.5 rounded-full text-xs font-medium hover:bg-gray-50">View: List</button>
                        <button className="bg-white border border-gray-200 text-gray-600 px-4 py-1.5 rounded-full text-xs font-medium hover:bg-gray-50 flex items-center gap-1">
                            <Download className="w-3 h-3" /> Export Report
                        </button>
                    </div>
                </div>

                {/* Scatterplot Container */}
                <div className="relative h-[500px] w-full bg-white rounded-xl border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.03)] p-12 mb-12 ml-4">

                    {/* Y-Axis Label */}
                    <div className="absolute -left-12 top-1/2 -translate-y-1/2 -rotate-90 text-xs font-semibold text-gray-500 tracking-wide whitespace-nowrap">
                        Risk Score (0-100)
                    </div>

                    {/* X-Axis Label */}
                    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-xs font-semibold text-gray-500 tracking-wide">
                        Days Until Renewal (Urgency)
                    </div>

                    {/* Chart Area */}
                    <div className="relative w-full h-full border-l border-b border-gray-200">
                        {/* Grid Lines Y (Steps of 20) */}
                        {[0, 20, 40, 60, 80, 100].map(y => (
                            <div key={y} className="absolute w-full border-t border-gray-100" style={{ bottom: `${y}%`, left: 0 }}>
                                <span className="absolute -left-8 -top-2 text-[11px] font-medium text-gray-400 w-6 text-right font-sans">{y}</span>
                            </div>
                        ))}
                        {/* Grid Lines X (Steps of 50, mapped to 300 days) */}
                        {[0, 50, 100, 150, 200, 250, 300].map(val => {
                            const domPos = (val / 300) * 100;
                            return (
                                <div key={val} className="absolute h-full border-l border-gray-100" style={{ left: `${domPos}%`, bottom: 0 }}>
                                    <span className="absolute -bottom-7 -left-3 text-[11px] font-medium text-gray-400 font-sans">{val}</span>
                                </div>
                            );
                        })}

                        {/* Bubbles */}
                        {scatterData.map((item, i) => {
                            const leftPos = (item.x / 300) * 100;
                            const bottomPos = item.y;
                            const colors = getRiskColor(item.y);

                            // Adjust size scaling slightly for cleaner look
                            const size = item.r * 2.2;

                            return (
                                <div
                                    key={i}
                                    className={`absolute rounded-full cursor-pointer transition-all hover:scale-110 hover:z-50 border ${colors.bg.replace('bg-', 'bg-opacity-80 bg-')} ${colors.border}`}
                                    style={{
                                        left: `${leftPos}%`,
                                        bottom: `${bottomPos}%`,
                                        width: `${size}px`,
                                        height: `${size}px`,
                                        transform: 'translate(-50%, 50%)', // Center bubble on coordinate
                                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
                                    }}
                                >
                                    {/* Tooltip */}
                                    <div className="hidden group-hover:block absolute bottom-full mb-3 left-1/2 -translate-x-1/2 w-72 bg-white rounded-lg p-0 shadow-xl border border-gray-100 z-50 pointer-events-none overflow-hidden ring-1 ring-black/5">
                                        <div className={`px-4 py-2 border-b border-gray-50 flex justify-between items-center ${colors.bg.replace('500', '50').replace('600', '50')}`}>
                                            <h4 className="font-semibold text-sm text-gray-900">{item.label}</h4>
                                            <span className={`text-[10px] font-bold uppercase tracking-wider ${colors.text}`}>{item.risk}</span>
                                        </div>
                                        <div className="p-4 space-y-2.5">
                                            <div className="grid grid-cols-2 gap-y-2 text-xs">
                                                <div className="text-gray-500">Counterparty</div>
                                                <div className="text-right font-medium text-gray-900">{item.cp}</div>

                                                <div className="text-gray-500">Contract Value</div>
                                                <div className="text-right font-medium text-gray-900">{item.val}</div>

                                                <div className="text-gray-500">Renewal Date</div>
                                                <div className="text-right font-medium text-gray-900">{item.date}</div>
                                            </div>
                                            <div className="pt-2 border-t border-gray-50">
                                                <p className="text-xs text-gray-600 italic leading-relaxed">"{item.desc}"</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </section>
        </div>
    );
};

export default CalendarTab;
