import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Bell,
    ChevronDown,
    Search,
    PlusCircle,
    LayoutList,
    LayoutGrid,
    FileText,
    FileCheck,
    Loader2,
    ArrowRight,
    CloudUpload,
    Sparkles,
    Lock,
    Clock,
    Plus,
    AlertCircle
} from 'lucide-react';
import api from '../services/api';

interface Review {
    review_id: string;
    contract_type: string;
    safety_score: number;
    total_findings: number;
    critical_count: number;
    good_count: number;
    negotiable_count: number;
    missing_count: number;
    created_at: string;
}

const Dashboard = () => {
    const navigate = useNavigate();
    const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
    const [activeFilter, setActiveFilter] = useState('all');
    const [selectedDocType, setSelectedDocType] = useState('nda');
    const [contextOpen, setContextOpen] = useState(false);

    // Reviews state
    const [reviews, setReviews] = useState<Review[]>([]);
    const [loadingReviews, setLoadingReviews] = useState(true);
    const [reviewsError, setReviewsError] = useState<string | null>(null);

    // Fetch reviews on component mount
    useEffect(() => {
        const fetchReviews = async () => {
            try {
                setLoadingReviews(true);
                const response = await api.get('/api/reviews');
                setReviews(response.data);
                setReviewsError(null);
            } catch (err: any) {
                console.error('Error fetching reviews:', err);
                setReviewsError(err.response?.data?.detail || 'Failed to load reviews');
            } finally {
                setLoadingReviews(false);
            }
        };

        fetchReviews();
    }, []);

    // Helper function to get risk level based on safety score
    const getRiskLevel = (score: number) => {
        if (score >= 80) return { label: 'Low Risk', bg: 'bg-[#DCFCE7]', text: 'text-[#166534]', border: 'border-[#BBF7D0]' };
        if (score >= 60) return { label: 'Medium Risk', bg: 'bg-[#FEF3C7]', text: 'text-[#92400E]', border: 'border-[#FDE68A]' };
        return { label: 'High Risk', bg: 'bg-[#FFE4E6]', text: 'text-[#9F1239]', border: 'border-[#FECDD3]' };
    };

    // Helper function to format time ago
    const getTimeAgo = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 60) return `${diffMins} min${diffMins !== 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hr${diffHours !== 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
        return date.toLocaleDateString();
    };

    // Helper function to navigate to review
    const handleReviewClick = (reviewId: string) => {
        navigate(`/split/${reviewId}`);
    };

    return (
        <div className="min-h-screen flex flex-col">
            {/* Background Gradients */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] bg-rose-50/60 rounded-full blur-[100px]"></div>
                <div className="absolute bottom-[0%] left-[-10%] w-[500px] h-[500px] bg-gray-100/50 rounded-full blur-[100px]"></div>
            </div>

            {/* Header Bar */}
            <header className="fixed top-0 w-full z-50 glass-nav h-[60px] flex items-center justify-between px-6">
                {/* Brand */}
                <div className="flex items-center gap-2">

                    <span className="font-serif-italic text-xl tracking-wide">Overrule</span>
                </div>

                {/* Center Tabs */}
                <div className="hidden md:flex gap-8 text-sm font-medium">
                    <a href="#" className="text-black border-b border-black pb-5 mt-5">Dashboard</a>
                    <a href="#" className="text-gray-400 hover:text-black transition-colors pb-5 mt-5">Library</a>
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
            <main className="relative z-10 flex-1 w-full max-w-[1400px] mx-auto pt-24 pb-12 px-6 grid grid-cols-1 lg:grid-cols-12 gap-8">

                {/* LEFT COLUMN: HISTORY */}
                <section className="lg:col-span-8 flex flex-col gap-6 animate-fade-up">

                    {/* Welcome Greeting */}
                    <div className="mb-2">
                        <h1 className="font-serif text-7xl md:text-8xl text-black tracking-tight">
                            Welcome, Riddhesh
                        </h1>
                        {/* <p className="text-gray-500 mt-2 font-light">
                            You have <span className="text-black font-medium">3 contracts</span> pending review
                        </p> */}
                    </div>

                    {/* Quick Actions Strip */}
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        {/* Start New Analysis Button */}
                        {/* Start New Analysis Button */}
                        <button className="w-full bg-black text-white rounded-2xl py-3 px-4 text-sm font-medium hover:bg-gray-900 transition-all flex items-center justify-center gap-2">
                            <PlusCircle className="w-4 h-4" />
                            <a href="/upload">Start new analysis</a>
                        </button>

                        {/* Search */}
                        <div className="relative flex-1 min-w-[240px]">
                            <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search documents and findings..."
                                className="search-input w-full rounded-full py-2 pl-10 pr-4 text-sm placeholder-gray-400"
                            />
                        </div>

                        {/* Filters */}
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setActiveFilter('all')}
                                className={`filter-chip px-4 py-1.5 rounded-full border text-xs font-medium ${activeFilter === 'all'
                                    ? 'bg-black text-white border-black'
                                    : 'border-gray-200 bg-white text-gray-600'
                                    }`}
                            >
                                All
                            </button>
                            <button
                                onClick={() => setActiveFilter('progress')}
                                className={`filter-chip px-4 py-1.5 rounded-full border text-xs font-medium ${activeFilter === 'progress'
                                    ? 'bg-black text-white border-black'
                                    : 'border-gray-200 bg-white text-gray-600'
                                    }`}
                            >
                                In Progress
                            </button>
                            <div className="h-4 w-[1px] bg-gray-300 mx-1"></div>
                            <button className="flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-black px-2">
                                Type <ChevronDown className="w-3 h-3" />
                            </button>
                            <button className="flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-black px-2">
                                Severity <ChevronDown className="w-3 h-3" />
                            </button>
                        </div>
                    </div>

                    {/* History Panel */}
                    <div className="glass-panel rounded-[32px] p-6 min-h-[500px] flex flex-col">

                        {/* Title Row */}
                        <div className="flex justify-between items-center mb-6 px-2">
                            <h2 className="font-serif text-2xl text-black">Recent analyses</h2>
                            <div className="flex bg-gray-100 rounded-lg p-1 gap-1">
                                <button
                                    onClick={() => setViewMode('list')}
                                    className={`p-1.5 rounded ${viewMode === 'list' ? 'bg-white shadow-sm text-black' : 'text-gray-400 hover:text-gray-600'}`}
                                >
                                    <LayoutList className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => setViewMode('grid')}
                                    className={`p-1.5 rounded ${viewMode === 'grid' ? 'bg-white shadow-sm text-black' : 'text-gray-400 hover:text-gray-600'}`}
                                >
                                    <LayoutGrid className="w-4 h-4" />
                                </button>
                            </div>
                        </div>

                        {/* TABLE HEADER */}
                        <div className="grid grid-cols-12 px-4 py-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">
                            <div className="col-span-5">Document</div>
                            <div className="col-span-3">Posture</div>
                            <div className="col-span-3">Findings</div>
                            <div className="col-span-1 text-right">Action</div>
                        </div>

                        {/* Dynamic Review Rows */}
                        {loadingReviews ? (
                            // Loading State
                            <div className="flex flex-col items-center justify-center py-12">
                                <Loader2 className="w-8 h-8 animate-spin text-gray-400 mb-3" />
                                <p className="text-sm text-gray-500">Loading reviews...</p>
                            </div>
                        ) : reviewsError ? (
                            // Error State
                            <div className="flex flex-col items-center justify-center py-12">
                                <AlertCircle className="w-8 h-8 text-red-400 mb-3" />
                                <p className="text-sm text-gray-600 mb-2">Failed to load reviews</p>
                                <p className="text-xs text-gray-400">{reviewsError}</p>
                            </div>
                        ) : reviews.length === 0 ? (
                            // Empty State
                            <div className="flex flex-col items-center justify-center py-12">
                                <FileText className="w-12 h-12 text-gray-300 mb-3" />
                                <p className="text-sm text-gray-600 mb-2">No reviews yet</p>
                                <p className="text-xs text-gray-400">Upload a document to get started</p>
                            </div>
                        ) : (
                            // Review List
                            reviews.map((review) => {
                                const riskLevel = getRiskLevel(review.safety_score);
                                return (
                                    <div
                                        key={review.review_id}
                                        onClick={() => handleReviewClick(review.review_id)}
                                        className="history-row bg-white/60 border border-gray-100 rounded-xl p-4 grid grid-cols-12 items-center mb-3 cursor-pointer group"
                                    >
                                        <div className="col-span-5 flex items-start gap-3">
                                            <div className="w-10 h-10 bg-white border border-gray-100 rounded-lg flex items-center justify-center text-gray-500 shadow-sm">
                                                <FileCheck className="w-5 h-5" />
                                            </div>
                                            <div>
                                                <h3 className="text-sm font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                                                    {review.contract_type.toUpperCase()} Contract
                                                </h3>
                                                <p className="text-[11px] text-gray-500 mt-0.5">
                                                    {review.contract_type} • {getTimeAgo(review.created_at)}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="col-span-3">
                                            <span className={`inline-flex items-center gap-1.5 ${riskLevel.bg} ${riskLevel.text} px-2.5 py-1 rounded-md text-[11px] font-semibold border ${riskLevel.border}`}>
                                                {riskLevel.label}
                                            </span>
                                            <div className="text-[10px] text-gray-400 mt-1 pl-1">Score: {review.safety_score}</div>
                                        </div>
                                        <div className="col-span-3 flex gap-2">
                                            {review.critical_count > 0 ? (
                                                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[#FFE4E6] text-[#9F1239] text-[10px] font-bold border border-[#FECDD3]" title="Critical">
                                                    {review.critical_count}
                                                </span>
                                            ) : (
                                                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-300 text-[10px] font-bold border border-gray-200">0</span>
                                            )}
                                            {review.negotiable_count > 0 ? (
                                                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[#FEF3C7] text-[#92400E] text-[10px] font-bold border border-[#FDE68A]" title="Negotiable">
                                                    {review.negotiable_count}
                                                </span>
                                            ) : (
                                                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-300 text-[10px] font-bold border border-gray-200">0</span>
                                            )}
                                            {review.good_count > 0 ? (
                                                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[#DCFCE7] text-[#166534] text-[10px] font-bold border border-[#BBF7D0]" title="Good">
                                                    {review.good_count}
                                                </span>
                                            ) : (
                                                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-300 text-[10px] font-bold border border-gray-200">0</span>
                                            )}
                                        </div>
                                        <div className="col-span-1 flex justify-end">
                                            <button className="opacity-0 group-hover:opacity-100 transition-opacity p-2 hover:bg-gray-100 rounded-full">
                                                <ArrowRight className="w-4 h-4 text-gray-600" />
                                            </button>
                                        </div>
                                    </div>
                                );
                            })
                        )}

                    </div>
                </section>

                {/* RIGHT COLUMN: NEW ANALYSIS */}
                <section className="lg:col-span-4 animate-fade-up delay-100">
                    <div className="bg-white rounded-[32px] shadow-[0_20px_40px_-10px_rgba(0,0,0,0.08)] border border-gray-100 p-8 h-full flex flex-col relative overflow-hidden">

                        {/* Decorative BG blob inside card */}
                        <div className="absolute top-0 right-0 w-32 h-32 bg-gray-50 rounded-bl-full -mr-8 -mt-8 pointer-events-none"></div>

                        <h2 className="font-serif text-3xl text-black mb-6 relative z-10">Start new analysis</h2>

                        {/* Upload Area */}
                        <div className="upload-zone w-full h-32 rounded-2xl flex flex-col items-center justify-center cursor-pointer mb-6 group">
                            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-sm mb-2 group-hover:scale-110 transition-transform">
                                <CloudUpload className="w-5 h-5 text-gray-600" />
                            </div>
                            <p className="text-xs font-medium text-gray-900">Drop PDF or DOCX here</p>
                            <p className="text-[10px] text-gray-400 mt-1">or click to browse</p>
                        </div>

                        {/* Document Type */}
                        <div className="mb-6">
                            <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-3">
                                Document Type
                            </label>
                            <div className="flex flex-wrap gap-2">
                                {['nda', 'msa', 'sow', 'policy', 'other'].map((type) => (
                                    <label key={type} className="cursor-pointer">
                                        <input
                                            type="radio"
                                            name="doctype"
                                            checked={selectedDocType === type}
                                            onChange={() => setSelectedDocType(type)}
                                            className="peer sr-only"
                                        />
                                        <div className="px-3 py-1.5 rounded-lg border border-gray-200 bg-white text-[11px] font-medium text-gray-600 peer-checked:bg-black peer-checked:text-white peer-checked:border-black transition-all uppercase">
                                            {type}
                                        </div>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* Context Accordion */}
                        <div className="mb-8 border-t border-b border-gray-100 py-2">
                            <div className="cursor-pointer" onClick={() => setContextOpen(!contextOpen)}>
                                <div className="flex items-center justify-between text-xs font-medium text-gray-500 py-2 hover:text-black transition-colors">
                                    Add Basic Context (Optional)
                                    <Plus className={`w-3 h-3 transition-transform ${contextOpen ? 'rotate-45' : ''}`} />
                                </div>
                                {contextOpen && (
                                    <div className="pt-2 pb-2 space-y-3">
                                        <div>
                                            <label className="text-[10px] text-gray-400 block mb-1">My Role</label>
                                            <select className="w-full bg-gray-50 border border-gray-200 rounded-lg text-xs p-2 outline-none focus:border-black">
                                                <option>Select role...</option>
                                                <option>Buyer / Customer</option>
                                                <option>Seller / Provider</option>
                                            </select>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* CTA */}
                        <button className="w-full bg-black text-white py-3.5 rounded-xl font-medium text-sm hover:bg-gray-800 hover:scale-[1.02] transition-all shadow-lg shadow-gray-200 flex items-center justify-center gap-2 mb-6">
                            Analyze Document <Sparkles className="w-3 h-3 text-yellow-200" />
                        </button>

                        {/* Footer Microcopy */}
                        <div className="mt-auto flex flex-col gap-3">
                            <div className="flex items-center gap-2 text-[10px] text-gray-400">
                                <Lock className="w-3 h-3" /> Private by default. Zero retention.
                            </div>
                            <div className="flex items-center gap-2 text-[10px] text-gray-400">
                                <Clock className="w-3 h-3" /> Avg time: &lt; 90s
                            </div>

                            {/* Quick Link */}
                            <div className="pt-4 mt-2 border-t border-gray-100">
                                <p className="text-[10px] text-gray-400 uppercase tracking-widest mb-2">Jump back in</p>
                                <a href="#" className="flex items-center gap-2 text-xs font-medium text-gray-700 hover:text-black">
                                    <span className="w-1.5 h-1.5 bg-rose-500 rounded-full animate-pulse"></span>
                                    Resume: Employment_Draft_v2
                                </a>
                            </div>
                        </div>

                    </div>
                </section>

            </main>

            <style>{`
        body {
          font-family: 'Inter', sans-serif;
          background-color: #FDFBF7;
          color: #1a1a1a;
        }

        .glass-nav {
          background: rgba(253, 251, 247, 0.85);
          backdrop-filter: blur(20px);
          border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }

        .search-input {
          background: rgba(255, 255, 255, 0.6);
          border: 1px solid rgba(0, 0, 0, 0.06);
          transition: all 0.2s;
        }

        .search-input:focus {
          background: white;
          border-color: #000;
          outline: none;
        }

        .filter-chip {
          transition: all 0.2s;
        }

        .filter-chip:hover {
          background: rgba(0, 0, 0, 0.03);
        }

        .history-row {
          transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
        }

        .history-row:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.05);
          background-color: white;
          z-index: 10;
        }

        .upload-zone {
          background-image: url("data:image/svg+xml,%3csvg width='100%25' height='100%25' xmlns='http://www.w3.org/2000/svg'%3e%3crect width='100%25' height='100%25' fill='none' rx='16' ry='16' stroke='%23D4D4D8FF' stroke-width='1' stroke-dasharray='8%2c 8' stroke-dashoffset='0' stroke-linecap='square'/%3e%3c/svg%3e");
          transition: all 0.3s;
        }

        .upload-zone:hover {
          background-color: #F9FAFB;
          background-image: url("data:image/svg+xml,%3csvg width='100%25' height='100%25' xmlns='http://www.w3.org/2000/svg'%3e%3crect width='100%25' height='100%25' fill='none' rx='16' ry='16' stroke='%23000000FF' stroke-width='1' stroke-dasharray='8%2c 8' stroke-dashoffset='0' stroke-linecap='square'/%3e%3c/svg%3e");
        }
      `}</style>
        </div>
    );
};

export default Dashboard;
