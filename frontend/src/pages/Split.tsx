import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
    Check,
    ShieldAlert,
    Coins,
    ChevronLeft,
    ChevronRight,
    Search,
    Wand2,
    Plus
} from 'lucide-react';
import api from '../services/api';

interface Step {
    label: string;
    status: 'complete' | 'active' | 'pending';
    detail?: string;
}

function Split() {
    const location = useLocation();
    const { file, purpose, context } = location.state || {};

    const [showResults, setShowResults] = useState(false);
    const [steps, setSteps] = useState<Step[]>([
        { label: 'Retrieving resources', status: 'pending' },
        { label: 'Parsing document structure', status: 'pending' },
        { label: 'Risk Assessment (Agent 1)', status: 'pending' },
        { label: 'Compliance Check (Agent 2)', status: 'pending' },
        { label: 'Financial Review (Agent 3)', status: 'pending' },
        { label: 'Final Judge Synthesis', status: 'pending' }
    ]);
    const [currentStepIndex, setCurrentStepIndex] = useState(-1);
    const [logEntry, setLogEntry] = useState('Initializing neural council...');
    const [apiComplete, setApiComplete] = useState(false);
    const [apiError, setApiError] = useState<string | null>(null);

    // Make API call on component mount
    useEffect(() => {
        const makeApiCall = async () => {
            if (!file) {
                setApiError('No file provided');
                setApiComplete(true);
                return;
            }

            try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('purpose', purpose || 'review');
                if (context) {
                    formData.append('context', context);
                }

                const response = await api.post('/api/review', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                });

                console.log('Review response:', response.data);
                setApiComplete(true);
            } catch (err: any) {
                console.error('Error generating review:', err);
                setApiError(err.response?.data?.detail || 'Failed to generate review');
                setApiComplete(true);
            }
        };

        makeApiCall();
    }, [file, purpose, context]);

    // Handle step-by-step animation with delays
    useEffect(() => {
        const STEP_DELAY = 2000; // 2 seconds between each step

        const interval = setInterval(() => {
            setCurrentStepIndex((prevIndex) => {
                const newIndex = prevIndex + 1;

                // Check if we're at the last step
                if (newIndex >= steps.length - 1) {
                    // Start the final step but keep it loading until API completes
                    setSteps((prevSteps) => {
                        const updated = [...prevSteps];
                        if (prevIndex >= 0 && prevIndex < updated.length) {
                            updated[prevIndex].status = 'complete';
                        }
                        updated[newIndex].status = 'active';
                        updated[newIndex].detail = 'Processing...';
                        setLogEntry(`> Processing ${updated[newIndex].label}...`);
                        return updated;
                    });
                    clearInterval(interval);
                    return newIndex;
                }

                // Normal step progression
                setSteps((prevSteps) => {
                    const updated = [...prevSteps];
                    if (prevIndex >= 0) {
                        updated[prevIndex].status = 'complete';
                    }
                    updated[newIndex].status = 'active';
                    updated[newIndex].detail = 'Processing...';
                    setLogEntry(`> Processing ${updated[newIndex].label}...`);
                    return updated;
                });

                return newIndex;
            });
        }, STEP_DELAY);

        return () => clearInterval(interval);
    }, []);

    // Complete final step when API is done
    useEffect(() => {
        if (apiComplete && currentStepIndex === steps.length - 1) {
            setSteps((prevSteps) => {
                const updated = [...prevSteps];
                updated[steps.length - 1].status = 'complete';
                delete updated[steps.length - 1].detail;
                return updated;
            });

            // Show results after a short delay
            setTimeout(() => setShowResults(true), 500);
        }
    }, [apiComplete, currentStepIndex, steps.length]);

    const highlightPdf = (citationId: string) => {
        const target = document.getElementById(citationId + '-target');
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            target.style.transform = 'scale(1.02)';
        }
    };

    const removeHighlight = (citationId: string) => {
        const target = document.getElementById(citationId + '-target');
        if (target) {
            target.style.transform = 'scale(1)';
        }
    };

    const renderStepIcon = (step: Step, index: number) => {
        if (step.status === 'complete') {
            return (
                <div className="w-8 h-8 rounded-full bg-black flex items-center justify-center text-white border border-black shadow-sm z-10">
                    <Check className="w-3 h-3" />
                </div>
            );
        } else if (step.status === 'active') {
            return (
                <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center border border-gray-200 step-active-dot z-10">
                    <div className="w-2 h-2 bg-black rounded-full"></div>
                </div>
            );
        } else {
            return (
                <div className="w-8 h-8 rounded-full bg-[#f5f5f4] flex items-center justify-center text-gray-300 border border-gray-100 z-10">
                    <span className="text-[10px] font-mono">{index + 1}</span>
                </div>
            );
        }
    };

    if (!showResults) {
        // SCREEN 1: ANALYSIS PROGRESS
        return (
            <div className="h-screen w-full relative overflow-hidden">
                {/* Background Elements */}
                <div className="fixed inset-0 z-0 pointer-events-none">
                    <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-[#dcedf0] via-[#eef6f6] to-[#d8f0e9]"></div>
                    <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-purple-100/30 rounded-full mix-blend-multiply filter blur-[100px] animate-pulse"></div>
                    <div className="absolute bottom-[10%] right-[-5%] w-[600px] h-[600px] bg-teal-100/40 rounded-full mix-blend-multiply filter blur-[100px]"></div>
                </div>

                {/* Analysis Screen */}
                <section className="relative z-10 w-full h-full flex flex-col items-center justify-center p-4">
                    <div className="glass-panel w-full max-w-lg rounded-[40px] p-10 shadow-2xl shadow-gray-200/40">
                        {/* Header */}
                        <div className="mb-10 text-center md:text-left">
                            <h1 className="font-serif text-4xl text-black tracking-tight">Analyzing document</h1>
                            <div className="flex items-center gap-2 mt-3 text-xs font-medium text-gray-500 uppercase tracking-widest justify-center md:justify-start">
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-gray-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-black"></span>
                                </span>
                                Council in progress
                            </div>
                        </div>

                        {/* Stepper */}
                        <div className="space-y-0 relative pl-2">
                            {/* Line connector */}
                            <div className="absolute left-[23px] top-5 bottom-5 w-[1px] bg-gray-200 -z-10"></div>

                            {steps.map((step, index) => (
                                <div key={index} className="flex items-center gap-5 py-3 relative">
                                    {renderStepIcon(step, index)}
                                    <div className="flex-1">
                                        <div className="flex justify-between items-center">
                                            <span
                                                className={`text-sm ${step.status === 'complete'
                                                    ? 'text-gray-900 font-medium'
                                                    : step.status === 'active'
                                                        ? 'text-black font-medium'
                                                        : 'text-gray-400 font-light'
                                                    }`}
                                            >
                                                {step.label}
                                            </span>
                                        </div>
                                        {step.status === 'active' && step.detail && (
                                            <p className="text-[10px] text-gray-400 mt-1 font-mono">{step.detail}</p>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Live Logs */}
                        <div className="mt-10 pt-6 border-t border-gray-100">
                            <div className="flex items-center justify-between text-[10px] text-gray-400 font-mono tracking-wide">
                                <span>{logEntry}</span>
                                <span>12.4s elapsed</span>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        );
    }

    // SCREEN 2: RESULTS SPLIT VIEW
    return (
        <div className="h-screen w-full relative overflow-hidden bg-[#FDFBF7] fade-in">
            {/* Background Elements */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-[#dcedf0] via-[#eef6f6] to-[#d8f0e9]"></div>
                <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-purple-100/30 rounded-full mix-blend-multiply filter blur-[100px] animate-pulse"></div>
                <div className="absolute bottom-[10%] right-[-5%] w-[600px] h-[600px] bg-teal-100/40 rounded-full mix-blend-multiply filter blur-[100px]"></div>
            </div>

            <section className="relative z-10 w-full h-full flex flex-col">
                <div className="flex-1 flex overflow-hidden">
                    {/* LEFT PANEL: PDF VIEWER (58%) */}
                    <div className="w-full md:w-[58%] bg-[#F5F5F4] flex flex-col relative border-r border-gray-200">
                        {/* Minimal Toolbar */}
                        <div className="h-14 bg-white/80 backdrop-blur border-b border-gray-200 flex items-center justify-between px-6 z-20">
                            <div className="flex items-center gap-4 text-gray-400">
                                <div className="flex items-center gap-3 bg-gray-50 rounded-lg px-2 py-1 border border-gray-100">
                                    <ChevronLeft className="w-3 h-3 cursor-pointer hover:text-black transition-colors" />
                                    <span className="text-[10px] font-mono text-gray-600">Pg 1 / 5</span>
                                    <ChevronRight className="w-3 h-3 cursor-pointer hover:text-black transition-colors" />
                                </div>
                            </div>
                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-yellow-200"></div>
                                    <span className="text-[10px] text-gray-500 font-medium">Citations On</span>
                                </div>
                                <Search className="w-4 h-4 text-gray-400 hover:text-black cursor-pointer transition-colors" />
                            </div>
                        </div>

                        {/* PDF Canvas */}
                        <div className="flex-1 overflow-y-auto custom-scroll p-8 flex justify-center scroll-smooth">
                            <div className="bg-white shadow-[0_20px_60px_-15px_rgba(0,0,0,0.1)] w-full max-w-[700px] min-h-[1000px] p-12 text-justify relative border border-gray-100">
                                {/* Header */}
                                <div className="flex justify-between items-end border-b border-gray-900 pb-6 mb-10">
                                    <h1 className="text-xl font-serif font-bold tracking-wide text-black">
                                        MASTER SERVICES AGREEMENT
                                    </h1>
                                    <span className="text-[10px] font-mono text-gray-400 uppercase">Ref: 2024-OV-88</span>
                                </div>

                                {/* Document Text */}
                                <div className="space-y-8 text-[12px] leading-[1.8] text-gray-700 font-serif">
                                    <p>
                                        This Master Services Agreement ("Agreement") is entered into as of{' '}
                                        <span className="bg-gray-100 px-1 rounded">[Date]</span>, by and between the parties listed below.
                                    </p>

                                    <div>
                                        <h4 className="font-bold text-black uppercase text-[10px] tracking-widest mb-2">1. Services</h4>
                                        <p>
                                            Provider agrees to perform the services described in one or more Statements of Work attached
                                            hereto as Exhibit A.
                                        </p>
                                    </div>

                                    {/* Section with Highlight */}
                                    <div id="citation-2-target" className="transition-all duration-700 rounded px-2 -mx-2">
                                        <h4 className="font-bold text-black uppercase text-[10px] tracking-widest mb-2">
                                            4. Term and Termination
                                        </h4>
                                        <p>
                                            The term of this Agreement shall commence on the Effective Date and continue for a period of two
                                            (2) years.{' '}
                                            <span className="bg-[#FEF3C7] border-b border-[#F59E0B] text-black">
                                                This Agreement shall automatically renew for successive one-year terms unless either party
                                                provides written notice.
                                            </span>
                                        </p>
                                    </div>

                                    {/* Critical Highlight */}
                                    <div id="citation-1-target" className="transition-all duration-700 rounded px-2 -mx-2">
                                        <h4 className="font-bold text-black uppercase text-[10px] tracking-widest mb-2">
                                            8. Indemnification
                                        </h4>
                                        <p>
                                            Client agrees to indemnify, defend, and hold harmless Provider from any claims arising out of
                                            Client's use of services.{' '}
                                            <span className="bg-[#FFE4E6] border-b border-[#E11D48] text-black font-medium">
                                                Provider's total liability under this agreement regarding any claim shall not exceed the total
                                                fees paid by Client in the preceding twelve (12) months.
                                            </span>{' '}
                                            However, Client's liability for indemnification shall remain unlimited.
                                        </p>
                                    </div>

                                    <div>
                                        <h4 className="font-bold text-black uppercase text-[10px] tracking-widest mb-2">
                                            9. Confidentiality
                                        </h4>
                                        <p>
                                            Each party agrees to hold the other party's Confidential Information in strict confidence and not
                                            to disclose such information to any third party without prior written consent.
                                        </p>
                                    </div>

                                    {/* Blurred content */}
                                    <div className="opacity-20 blur-[1px] select-none">
                                        <p>
                                            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut
                                            labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris
                                            nisi ut aliquip ex ea commodo consequat.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* RIGHT PANEL: VERDICT & INSIGHTS (42%) */}
                    <div className="w-full md:w-[42%] flex flex-col bg-white/60 backdrop-blur-sm">
                        {/* Scrollable Content */}
                        <div className="flex-1 overflow-y-auto custom-scroll p-6">
                            {/* Verdict Card */}
                            <div className="bg-[#fafaf9] border border-gray-200 rounded-2xl p-8 mb-8 relative overflow-hidden group">
                                {/* Subtle decorative gradient */}
                                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-gray-100 to-transparent rounded-bl-full -mr-8 -mt-8 opacity-50"></div>

                                <div className="relative z-10">
                                    <div className="flex justify-between items-start mb-5">
                                        <div>
                                            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                                                Final Verdict
                                            </span>
                                            <h2 className="font-serif text-4xl text-black mt-2 leading-tight">
                                                Balanced with
                                                <br />
                                                <span className="font-serif-italic text-gray-600">specific risks</span>
                                            </h2>
                                        </div>
                                        <div className="bg-black text-white text-xs font-medium px-4 py-1.5 rounded-full shadow-lg">
                                            Score: 78
                                        </div>
                                    </div>

                                    <p className="text-sm text-gray-600 font-light leading-relaxed mb-6">
                                        The agreement adheres to standard terms but contains{' '}
                                        <span className="font-medium text-black">uncapped indemnity</span> and ambiguous IP clauses. We
                                        recommend specific redlines before signing.
                                    </p>

                                    {/* Tags */}
                                    <div className="flex flex-wrap gap-2 mb-6">
                                        <span className="px-3 py-1 bg-[#F5F5F4] text-gray-600 rounded-lg text-[11px] font-medium border border-gray-100">
                                            Buyer-friendly
                                        </span>
                                        <span className="px-3 py-1 bg-[#FFF1F2] text-[#9F1239] rounded-lg text-[11px] font-medium border border-[#FFE4E6]">
                                            Data Privacy Gaps
                                        </span>
                                    </div>

                                    {/* Action Buttons */}
                                    <div className="flex items-center gap-3">
                                        <button className="flex-1 bg-[#166534] text-white text-xs font-serif px-5 py-2.5 rounded-xl hover:bg-[#14532d] transition-all">
                                            Correct agent
                                        </button>
                                        <button className="flex-1 bg-[#166534] text-white text-xs font-serif px-5 py-2.5 rounded-xl hover:bg-[#14532d] transition-all flex items-center justify-center gap-2">
                                            <Wand2 className="w-3 h-3" /> Refine contract
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Highlights Section */}
                            <div className="mb-8">
                                {/* Minimal Tabs */}
                                <div className="flex gap-6 border-b border-gray-100 mb-6 pb-1">
                                    <button className="text-sm font-medium text-black border-b border-black pb-1">Critical (1)</button>
                                    <button className="text-sm font-medium text-gray-400 hover:text-gray-600 pb-1 transition-colors">
                                        Negotiables (3)
                                    </button>
                                    <button className="text-sm font-medium text-gray-400 hover:text-gray-600 pb-1 transition-colors">
                                        Positives (4)
                                    </button>
                                </div>

                                {/* Findings Cards */}
                                <div className="space-y-4">
                                    {/* Card 1 */}
                                    <div
                                        className="group bg-white border border-gray-100 rounded-xl p-5 shadow-[0_2px_8px_rgba(0,0,0,0.02)] hover:shadow-[0_8px_16px_rgba(0,0,0,0.04)] hover:border-gray-200 transition-all cursor-pointer relative overflow-hidden"
                                        onMouseEnter={() => highlightPdf('citation-1')}
                                        onMouseLeave={() => removeHighlight('citation-1')}
                                    >
                                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#FECDD3]"></div>

                                        <div className="pl-2">
                                            <div className="flex justify-between items-start mb-2">
                                                <h3 className="font-medium text-black text-sm">Uncapped Indemnity</h3>
                                                <span className="bg-[#FFF1F2] text-[#be123c] text-[10px] font-semibold px-2 py-0.5 rounded">
                                                    CRITICAL
                                                </span>
                                            </div>
                                            <p className="text-xs text-gray-500 font-light leading-relaxed mb-4">
                                                The indemnity clause lacks a liability cap, exposing you to unlimited financial risk.
                                            </p>
                                            <div className="flex gap-4 opacity-0 group-hover:opacity-100 transition-opacity translate-y-2 group-hover:translate-y-0 duration-300">
                                                <button className="text-[10px] font-medium text-black border-b border-black/20 hover:border-black">
                                                    View citation
                                                </button>
                                                <button className="text-[10px] font-medium text-gray-400 hover:text-black transition-colors">
                                                    Edit
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Card 2 */}
                                    <div
                                        className="group bg-white border border-gray-100 rounded-xl p-5 shadow-[0_2px_8px_rgba(0,0,0,0.02)] hover:shadow-[0_8px_16px_rgba(0,0,0,0.04)] hover:border-gray-200 transition-all cursor-pointer relative overflow-hidden"
                                        onMouseEnter={() => highlightPdf('citation-2')}
                                        onMouseLeave={() => removeHighlight('citation-2')}
                                    >
                                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#FDE68A]"></div>

                                        <div className="pl-2">
                                            <div className="flex justify-between items-start mb-2">
                                                <h3 className="font-medium text-black text-sm">Termination Convenience</h3>
                                                <span className="bg-[#FFFBEB] text-[#B45309] text-[10px] font-semibold px-2 py-0.5 rounded">
                                                    RISK
                                                </span>
                                            </div>
                                            <p className="text-xs text-gray-500 font-light leading-relaxed">
                                                Missing termination for convenience clause locks you into the full term.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Council Opinions */}
                            <div className="space-y-3">
                                <div className="text-[10px] font-bold text-gray-300 uppercase tracking-widest mb-3">
                                    Council Opinions
                                </div>

                                {/* Agent 1: Risk */}
                                <details className="group bg-[#FFF1F2] border border-[#FECDD3] rounded-xl" open>
                                    <summary className="flex items-center justify-between p-4 cursor-pointer list-none rounded-xl transition-colors">
                                        <div className="flex items-center gap-3">
                                            <div className="w-6 h-6 rounded-full bg-white flex items-center justify-center border border-[#FECDD3]">
                                                <ShieldAlert className="w-3 h-3 text-[#BE123C]" />
                                            </div>
                                            <span className="text-xs font-semibold text-[#881337]">Agent Risk</span>
                                        </div>
                                        <Plus className="w-3 h-3 text-[#9F1239] group-open:rotate-45 transition-transform" />
                                    </summary>
                                    <div className="px-4 pb-4 pt-0">
                                        <p className="text-[11px] text-[#9F1239] leading-relaxed pl-9">
                                            Strongly advise rejecting Section 8.2 due to lack of mutual indemnification. This is non-standard
                                            for your jurisdiction.
                                        </p>
                                    </div>
                                </details>

                                {/* Agent 2: Finance */}
                                <details className="group bg-[#F0FDF4] border border-[#BBF7D0] rounded-xl">
                                    <summary className="flex items-center justify-between p-4 cursor-pointer list-none rounded-xl transition-colors">
                                        <div className="flex items-center gap-3">
                                            <div className="w-6 h-6 rounded-full bg-white flex items-center justify-center border border-[#BBF7D0]">
                                                <Coins className="w-3 h-3 text-[#15803D]" />
                                            </div>
                                            <span className="text-xs font-semibold text-[#14532D]">Agent Finance</span>
                                        </div>
                                        <Plus className="w-3 h-3 text-[#15803D] group-open:rotate-45 transition-transform" />
                                    </summary>
                                    <div className="px-4 pb-4 pt-0">
                                        <p className="text-[11px] text-[#14532D] leading-relaxed pl-9">
                                            Payment terms (Net 30) align with company fiscal policy. No issues detected.
                                        </p>
                                    </div>
                                </details>
                            </div>
                        </div>
                    </div>
                </div>


            </section>
        </div>
    );
}

export default Split;
