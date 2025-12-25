import React, { useState, useEffect } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import {
    Check,
    ShieldAlert,
    Coins,
    Wand2,
    Plus,
    Info,
    Sparkles,
    CornerDownLeft,
    Copy,
    Share2,
    ThumbsUp,
    ThumbsDown,
    Globe

} from 'lucide-react';
import api from '../services/api';
import { config } from '../config';

interface Step {
    label: string;
    status: 'complete' | 'active' | 'pending';
    detail?: string;
}

function Split() {
    const location = useLocation();
    const { reviewId } = useParams<{ reviewId: string }>();
    const navigate = useNavigate();
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

    // Review data from API
    const [reviewData, setReviewData] = useState<any>(null);
    const [activeTab, setActiveTab] = useState<'critical' | 'good' | 'missing' | 'negotiable'>('critical');
    const [rightPanelTab, setRightPanelTab] = useState<'analysis' | 'chat'>('analysis');
    const [showCorrectionInput, setShowCorrectionInput] = useState(false);
    const [correctionText, setCorrectionText] = useState('');
    const [showQueuePopup, setShowQueuePopup] = useState(false);
    const [showRefineInput, setShowRefineInput] = useState(false);
    const [refineChoice, setRefineChoice] = useState<'Balanced' | 'Unilateral' | ''>('');
    const [refineText, setRefineText] = useState('');

    // Translation State
    const [translation, setTranslation] = useState<{ text: string; lang: string } | null>(null);
    const [translating, setTranslating] = useState(false);
    const [showLanguageDropdown, setShowLanguageDropdown] = useState(false);


    // Feedback State
    type FeedbackState = {
        [key: string]: {
            type: 'up' | 'down' | null;
            correction?: string;
            comment?: string;
        }
    };
    const [feedback, setFeedback] = useState<FeedbackState>({});

    const getCardKey = (tab: string, index: number) => `${tab}-${index}`;

    const handleFeedback = (tab: string, index: number, type: 'up' | 'down') => {
        const key = getCardKey(tab, index);
        setFeedback(prev => ({
            ...prev,
            [key]: {
                ...prev[key],
                type: prev[key]?.type === type ? null : type // Toggle if same clicked
            }
        }));
    };

    const handleCorrectionChange = (tab: string, index: number, text: string) => {
        const key = getCardKey(tab, index);
        setFeedback(prev => ({
            ...prev,
            [key]: {
                ...prev[key],
                correction: text
            }
        }));
    };

    const submitCorrection = (tab: string, index: number) => {
        const key = getCardKey(tab, index);
        const currentCorrection = feedback[key]?.correction;
        if (!currentCorrection?.trim()) return;

        setFeedback(prev => ({
            ...prev,
            [key]: {
                ...prev[key],
                comment: currentCorrection, // Set the comment
                correction: '' // Clear the input draft
            }
        }));
    };

    // Helper to derive current review id
    const currentReviewId = reviewId || reviewData?.review_id;

    const downloadRefinedPdf = async () => {
        if (!currentReviewId) {
            setApiError('No review id available for export');
            return;
        }
        try {
            const response = await api.get(`/api/reviews/${currentReviewId}/export/pdf`, {
                responseType: 'blob'
            });
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            const disposition = response.headers['content-disposition'] || '';
            const match = disposition.match(/filename="?([^"]+)"?/i);
            const filename = match?.[1] || `review_${currentReviewId}_refined.pdf`;
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err: any) {
            setApiError(err.response?.data?.detail || 'Failed to export refined PDF');
        }
    };

    const handleTranslate = async (lang: string) => {
        if (!reviewData?.summary) return;

        try {
            setTranslating(true);
            setShowLanguageDropdown(false);
            const response = await api.post('/api/translate', {
                text: reviewData.summary,
                target_language: lang
            });
            setTranslation({
                text: response.data.translated_text,
                lang: lang
            });
        } catch (err: any) {
            console.error('Translation failed:', err);
            // Optional: Show error toast
        } finally {
            setTranslating(false);
        }
    };


    // Make API call on component mount
    useEffect(() => {
        const makeApiCall = async () => {
            // If reviewId is in URL, fetch existing review
            if (reviewId) {
                try {
                    const response = await api.get(`/api/reviews/${reviewId}`);
                    console.log('Fetched review:', response.data);

                    // Store review data
                    setReviewData(response.data);
                    setApiComplete(true);

                    // Skip animation, go straight to results
                    setCurrentStepIndex(steps.length - 1);
                    setSteps(prevSteps => prevSteps.map(step => ({ ...step, status: 'complete' })));
                    setShowResults(true);
                } catch (err: any) {
                    console.error('Error fetching review:', err);
                    setApiError(err.response?.data?.detail || 'Failed to fetch review');
                    setApiComplete(true);
                }
                return;
            }

            // Otherwise, create new review from uploaded file
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

                // Store review data
                const newReviewId = response.data.review_id;
                setReviewData(response.data);
                setApiComplete(true);

                // Update URL to include review_id (without triggering re-render)
                window.history.replaceState(null, '', `/split/${newReviewId}`);
            } catch (err: any) {
                console.error('Error generating review:', err);
                setApiError(err.response?.data?.detail || 'Failed to generate review');
                setApiComplete(true);
            }
        };

        makeApiCall();
    }, [reviewId, file, purpose, context, steps.length]);

    // Handle step-by-step animation with delays
    useEffect(() => {
        const STEP_DELAY = 2000; // 2 seconds between each step

        const interval = setInterval(() => {
            setCurrentStepIndex((prevIndex) => {
                // If we are already at the last step (e.g. from API completion), stop
                if (prevIndex >= steps.length - 1) {
                    clearInterval(interval);
                    return prevIndex;
                }

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

    // Helper function to get findings for active tab
    const getActiveFindings = () => {
        if (!reviewData) return [];
        switch (activeTab) {
            case 'critical': return reviewData.critical_points || [];
            case 'good': return reviewData.good_points || [];
            case 'missing': return reviewData.missing_points || [];
            case 'negotiable': return reviewData.negotiable_points || [];
            default: return [];
        }
    };

    // Helper function to get color scheme for each category
    const getCategoryColors = (category: string) => {
        const colors = {
            critical: { bg: 'bg-[#FFF1F2]', text: 'text-[#be123c]', border: 'border-[#FFE4E6]', leftBar: 'bg-[#FECDD3]' },
            good: { bg: 'bg-[#F0FDF4]', text: 'text-[#15803D]', border: 'border-[#BBF7D0]', leftBar: 'bg-[#BBF7D0]' },
            missing: { bg: 'bg-[#FEF3C7]', text: 'text-[#B45309]', border: 'border-[#FDE68A]', leftBar: 'bg-[#FDE68A]' },
            negotiable: { bg: 'bg-[#EFF6FF]', text: 'text-[#1E40AF]', border: 'border-[#DBEAFE]', leftBar: 'bg-[#DBEAFE]' }
        };
        return colors[category as keyof typeof colors] || colors.critical;
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


                        {/* PDF Canvas */}
                        <div className="flex-1 overflow-y-auto custom-scroll bg-gray-100">
                            {(reviewId || reviewData?.review_id) ? (
                                <iframe
                                    src={`${config.apiBaseUrl}/api/reviews/${reviewId || reviewData?.review_id}/annotated-pdf`}
                                    className="w-full h-full border-0"
                                    style={{ minHeight: '800px' }}
                                    title="Annotated PDF"
                                />
                            ) : (
                                <div className="flex items-center justify-center h-full">
                                    <p className="text-gray-400 text-sm">Loading annotated PDF...</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* RIGHT PANEL: VERDICT & INSIGHTS (42%) */}
                    <div className="w-full md:w-[42%] flex flex-col bg-white/60 backdrop-blur-sm">
                        {/* Tab Header */}
                        <div className="flex border-b border-gray-200 bg-white/50 backdrop-blur-sm sticky top-0 z-20">
                            <button
                                onClick={() => setRightPanelTab('analysis')}
                                className={`flex-1 py-4 text-sm font-semibold transition-all relative ${rightPanelTab === 'analysis'
                                    ? 'text-[#064E3B]'
                                    : 'text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                Analysis
                                {rightPanelTab === 'analysis' && (
                                    <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#064E3B]"></div>
                                )}
                            </button>
                            <button
                                onClick={() => setRightPanelTab('chat')}
                                className={`flex-1 py-4 text-sm font-semibold transition-all relative ${rightPanelTab === 'chat'
                                    ? 'text-[#064E3B]'
                                    : 'text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                Chat Assistant
                                {rightPanelTab === 'chat' && (
                                    <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#064E3B]"></div>
                                )}
                            </button>
                        </div>

                        {rightPanelTab === 'analysis' ? (
                            /* ANALYSIS CONTENT */
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
                                                    {'Analysis Complete'}
                                                </h2>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                {/* Language Dropdown */}
                                                <div className="relative">
                                                    <button
                                                        onClick={() => setShowLanguageDropdown(!showLanguageDropdown)}
                                                        className="flex items-center gap-2 bg-white border border-gray-200 text-gray-600 text-xs font-medium px-3 py-2 rounded-full hover:bg-gray-50 transition-all"
                                                    >
                                                        <Globe className="w-3.5 h-3.5" />
                                                        {translation ? translation.lang : 'Translate'}
                                                    </button>

                                                    {showLanguageDropdown && (
                                                        <div className="absolute top-full right-0 mt-2 w-32 bg-white border border-gray-100 rounded-xl shadow-lg overflow-hidden z-50">
                                                            {['Hindi', 'Marathi', 'Tamil', 'Gujarati'].map((lang) => (
                                                                <button
                                                                    key={lang}
                                                                    onClick={() => handleTranslate(lang)}
                                                                    className="w-full text-left px-4 py-2 text-xs hover:bg-gray-50 text-gray-700 transition-colors"
                                                                >
                                                                    {lang}
                                                                </button>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>

                                                <div className="relative group/share">
                                                    <button
                                                        onClick={downloadRefinedPdf}
                                                        className="flex items-center gap-2 bg-[#0C4522] text-white text-xs font-medium px-4 py-2 rounded-full shadow-lg hover:bg-[#09361a] transition-all"
                                                    >
                                                        <Share2 className="w-3.5 h-3.5" />
                                                        Share
                                                    </button>
                                                    <div className="absolute bottom-full mb-2 right-0 w-max bg-gray-900 text-white text-[10px] px-2 py-1.5 rounded opacity-0 group-hover/share:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                                                        Redacted PDF will be created
                                                        <div className="absolute top-full right-4 border-4 border-transparent border-t-gray-900"></div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <p className="text-sm text-gray-600 font-light leading-relaxed mb-6">
                                            {reviewData?.summary}
                                        </p>

                                        {/* Translated Summary */}
                                        {translating && (
                                            <div className="text-sm text-gray-400 font-light italic mb-6 animate-pulse">
                                                Translating...
                                            </div>
                                        )}
                                        {translation && !translating && (
                                            <div className="bg-gray-50 border border-gray-100 rounded-xl p-4 mb-6">
                                                <div className="text-[10px] font-bold text-gray-400 uppercase mb-2">
                                                    Translated to {translation.lang}
                                                </div>
                                                <p className="text-sm text-gray-700 font-light leading-relaxed">
                                                    {translation.text}
                                                </p>
                                            </div>
                                        )}
                                        <p className="text-sm text-gray-600 font-light leading-relaxed mb-6">
                                            {`We found ${reviewData?.total_findings || 0} points of interest in your document. Review the details below.`}
                                        </p>

                                        {/* Total Findings */}
                                        <div className="flex flex-wrap gap-2 mb-6">
                                            {(reviewData?.critical_points?.length || 0) > 0 && (
                                                <span className="px-3 py-1 bg-[#FFF1F2] text-[#9F1239] rounded-lg text-[11px] font-medium border border-[#FFE4E6]">
                                                    {reviewData.critical_points.length} Critical
                                                </span>
                                            )}
                                            {(reviewData?.good_points?.length || 0) > 0 && (
                                                <span className="px-3 py-1 bg-[#F0FDF4] text-[#15803D] rounded-lg text-[11px] font-medium border border-[#BBF7D0]">
                                                    {reviewData.good_points.length} Good
                                                </span>
                                            )}
                                            {(reviewData?.missing_points?.length || 0) > 0 && (
                                                <span className="px-3 py-1 bg-[#FEF3C7] text-[#B45309] rounded-lg text-[11px] font-medium border border-[#FDE68A]">
                                                    {reviewData.missing_points.length} Missing
                                                </span>
                                            )}
                                            {(reviewData?.negotiable_points?.length || 0) > 0 && (
                                                <span className="px-3 py-1 bg-[#EFF6FF] text-[#1E40AF] rounded-lg text-[11px] font-medium border border-[#DBEAFE]">
                                                    {reviewData.negotiable_points.length} Negotiable
                                                </span>
                                            )}
                                        </div>

                                        {/* Action Buttons */}
                                        <div className="flex items-center gap-3">
                                            <button
                                                onClick={() => {
                                                    setShowCorrectionInput(true);
                                                    setShowRefineInput(false);
                                                    setRefineChoice('');
                                                    setRefineText('');
                                                }}
                                                className="flex-1 bg-[#166534] text-white text-2xl font-serif px-5 py-2.5 rounded-xl hover:bg-[#14532d] transition-all"
                                            >
                                                Correct agent
                                            </button>
                                            <button
                                                onClick={() => {
                                                    setShowRefineInput(true);
                                                    setShowCorrectionInput(false);
                                                    setCorrectionText('');
                                                }}
                                                className="flex-1 bg-[#166534] text-white text-2xl font-serif px-5 py-2.5 rounded-xl hover:bg-[#14532d] transition-all flex items-center justify-center gap-2"
                                            >
                                                Refine contract
                                            </button>
                                        </div>
                                        {showCorrectionInput && (
                                            <div className="mt-4 space-y-3">
                                                <textarea
                                                    className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-black focus:outline-none"
                                                    rows={3}
                                                    placeholder="Type your correction..."
                                                    value={correctionText}
                                                    onChange={(e) => setCorrectionText(e.target.value)}
                                                />
                                                <button
                                                    onClick={() => {
                                                        console.log('Send correction:', correctionText);
                                                        setCorrectionText('');
                                                        setShowCorrectionInput(false);
                                                    }}
                                                    className="bg-[#166534] text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-[#14532d] transition-all"
                                                >
                                                    Send
                                                </button>
                                            </div>
                                        )}
                                        {showRefineInput && (
                                            <div className="mt-4 space-y-3">
                                                <div className="flex items-center gap-2 text-sm text-gray-700">
                                                    <span>How you wanna refine it?</span>
                                                    <div className="relative">
                                                        <button
                                                            onClick={() => setRefineChoice('Balanced')}
                                                            className={`px-4 py-2 rounded-lg border text-sm font-semibold flex items-center gap-1 ${refineChoice === 'Balanced' ? 'bg-[#166534] text-white border-[#166534]' : 'border-gray-200 text-gray-700'}`}
                                                        >
                                                            A. Balanced
                                                            <span className="relative group/info flex items-center">
                                                                <Info className="w-3.5 h-3.5" />
                                                                <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs rounded-lg py-1.5 px-3 whitespace-nowrap opacity-0 pointer-events-none group-hover/info:opacity-100 transition-opacity z-50">
                                                                    Balanced: aims for mutual fairness in obligations and benefits.
                                                                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                                                                </div>
                                                            </span>
                                                        </button>
                                                    </div>
                                                    <div className="relative">
                                                        <button
                                                            onClick={() => setRefineChoice('Unilateral')}
                                                            className={`px-4 py-2 rounded-lg border text-sm font-semibold flex items-center gap-1 ${refineChoice === 'Unilateral' ? 'bg-[#166534] text-white border-[#166534]' : 'border-gray-200 text-gray-700'}`}
                                                        >
                                                            B. Unilateral
                                                            <span className="relative group/info flex items-center">
                                                                <Info className="w-3.5 h-3.5" />
                                                                <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs rounded-lg py-1.5 px-3 whitespace-nowrap opacity-0 pointer-events-none group-hover/info:opacity-100 transition-opacity z-50">
                                                                    Unilateral: favors one party's position more heavily.
                                                                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                                                                </div>
                                                            </span>
                                                        </button>
                                                    </div>
                                                </div>
                                                <textarea
                                                    className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-black focus:outline-none"
                                                    rows={3}
                                                    placeholder="Anything other than missing, critical & negotiable?"
                                                    value={refineText}
                                                    onChange={(e) => setRefineText(e.target.value)}
                                                />
                                                <button
                                                    onClick={() => {
                                                        if (currentReviewId) {
                                                            window.open(`http://localhost:8000/api/reviews/${currentReviewId}/export/pdf`, '_blank');
                                                        }
                                                        setRefineChoice('');
                                                        setRefineText('');
                                                        setShowRefineInput(false);
                                                    }}
                                                    className="bg-[#166534] text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-[#14532d] transition-all"
                                                >
                                                    Send
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Highlights Section */}
                                <div className="mb-8">
                                    {/* Minimal Tabs */}
                                    <div className="flex gap-6 border-b border-gray-100 mb-6 pb-1">
                                        <button
                                            onClick={() => setActiveTab('critical')}
                                            className={`text-sm font-medium pb-1 transition-colors ${activeTab === 'critical'
                                                ? 'text-black border-b border-black'
                                                : 'text-gray-400 hover:text-gray-600'
                                                }`}
                                        >
                                            Critical ({reviewData?.critical_points?.length || 0})
                                        </button>
                                        <button
                                            onClick={() => setActiveTab('good')}
                                            className={`text-sm font-medium pb-1 transition-colors ${activeTab === 'good'
                                                ? 'text-black border-b border-black'
                                                : 'text-gray-400 hover:text-gray-600'
                                                }`}
                                        >
                                            Good ({reviewData?.good_points?.length || 0})
                                        </button>
                                        <button
                                            onClick={() => setActiveTab('missing')}
                                            className={`text-sm font-medium pb-1 transition-colors ${activeTab === 'missing'
                                                ? 'text-black border-b border-black'
                                                : 'text-gray-400 hover:text-gray-600'
                                                }`}
                                        >
                                            Missing ({reviewData?.missing_points?.length || 0})
                                        </button>
                                        <button
                                            onClick={() => setActiveTab('negotiable')}
                                            className={`text-sm font-medium pb-1 transition-colors ${activeTab === 'negotiable'
                                                ? 'text-black border-b border-black'
                                                : 'text-gray-400 hover:text-gray-600'
                                                }`}
                                        >
                                            Negotiable ({reviewData?.negotiable_points?.length || 0})
                                        </button>
                                    </div>

                                    {/* Findings Cards */}
                                    <div className="space-y-4">
                                        {getActiveFindings().length > 0 ? (
                                            getActiveFindings().map((finding: any, index: number) => {
                                                const colors = getCategoryColors(activeTab);
                                                return (
                                                    <div
                                                        key={index}
                                                        className="group bg-white border border-gray-100 rounded-xl p-5 shadow-[0_2px_8px_rgba(0,0,0,0.02)] hover:shadow-[0_8px_16px_rgba(0,0,0,0.04)] hover:border-gray-200 transition-all cursor-pointer relative overflow-hidden"
                                                    >
                                                        <div className={`absolute left-0 top-0 bottom-0 w-1 ${colors.leftBar}`}></div>

                                                        <div className="pl-2">
                                                            <div className="flex justify-between items-start mb-2">
                                                                <h3 className="font-medium text-black text-sm pr-2">{finding.advice}</h3>
                                                                <span className={`${colors.bg} ${colors.text} text-[10px] font-semibold px-2 py-0.5 rounded uppercase shrink-0`}>
                                                                    {activeTab}
                                                                </span>
                                                            </div>
                                                            <p className="text-xs text-gray-500 font-light leading-relaxed mb-3">
                                                                {finding.quote ? `"${finding.quote}"` : ''}
                                                            </p>

                                                            {/* Feedback Actions */}
                                                            <div className="flex flex-col gap-2">
                                                                <div className="flex items-center gap-3">
                                                                    <button
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            handleFeedback(activeTab, index, 'up');
                                                                        }}
                                                                        className={`p-1 rounded hover:bg-gray-100 transition-colors ${feedback[getCardKey(activeTab, index)]?.type === 'up' ? 'text-green-600' : 'text-gray-300'}`}
                                                                    >
                                                                        <ThumbsUp className="w-3.5 h-3.5" />
                                                                    </button>
                                                                    <button
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            handleFeedback(activeTab, index, 'down');
                                                                        }}
                                                                        className={`p-1 rounded hover:bg-gray-100 transition-colors ${feedback[getCardKey(activeTab, index)]?.type === 'down' ? 'text-red-500' : 'text-gray-300'}`}
                                                                    >
                                                                        <ThumbsDown className="w-3.5 h-3.5" />
                                                                    </button>
                                                                </div>

                                                                {/* Correction Input or Comment */}
                                                                {feedback[getCardKey(activeTab, index)]?.comment ? (
                                                                    <div className="mt-2 text-xs bg-gray-50 border border-gray-100 p-2 rounded text-gray-700 italic">
                                                                        Correction: "{feedback[getCardKey(activeTab, index)]?.comment}"
                                                                    </div>
                                                                ) : feedback[getCardKey(activeTab, index)]?.type === 'down' && (
                                                                    <div className="flex gap-2 mt-1" onClick={(e) => e.stopPropagation()}>
                                                                        <input
                                                                            type="text"
                                                                            placeholder="Correction..."
                                                                            value={feedback[getCardKey(activeTab, index)]?.correction || ''}
                                                                            onChange={(e) => handleCorrectionChange(activeTab, index, e.target.value)}
                                                                            className="flex-1 text-xs border border-gray-200 rounded px-2 py-1 focus:outline-none focus:border-gray-400"
                                                                            onKeyDown={(e) => {
                                                                                if (e.key === 'Enter') {
                                                                                    submitCorrection(activeTab, index);
                                                                                }
                                                                            }}
                                                                        />
                                                                        <button
                                                                            onClick={() => submitCorrection(activeTab, index)}
                                                                            className="bg-black text-white text-[10px] px-2 py-1 rounded hover:bg-gray-800 transition-colors"
                                                                        >
                                                                            Send
                                                                        </button>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            })
                                        ) : (
                                            <div className="text-center py-8 text-gray-400 text-sm">
                                                {reviewData ? `No ${activeTab} points found` : 'Loading findings...'}
                                            </div>
                                        )}
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
                        ) : (
                            /* CHAT ASSISTANT CONTENT */
                            <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#F8FAFC]">
                                {/* Chat Header Info */}
                                <div className="px-6 py-6 border-b border-gray-100 bg-white">
                                    <div className="flex items-start gap-3">
                                        <div className="w-10 h-10 rounded-full bg-[#166534] flex items-center justify-center text-white shrink-0 shadow-lg shadow-green-900/10">
                                            <Sparkles className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <h3 className="font-serif text-lg text-black">AI Assistant</h3>
                                            <p className="text-xs text-gray-500">Ask about clauses, risks, or redlines.</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Messages Area */}
                                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                                    {/* AI Message */}
                                    <div className="flex justify-start">
                                        <div className="bg-white rounded-2xl rounded-tl-sm p-5 shadow-sm border border-gray-100 max-w-[90%]">
                                            <p className="text-sm text-gray-800 leading-relaxed">
                                                I've analyzed the <span className="font-semibold text-black">Liability Agreement</span>. There are 11 critical risks, mostly concerning California Labor Code violations. How would you like to proceed?
                                            </p>
                                        </div>
                                    </div>

                                    {/* User Message */}
                                    <div className="flex justify-end">
                                        <div className="bg-[#0f172a] text-white rounded-2xl rounded-tr-sm p-4 shadow-md max-w-[90%]">
                                            <p className="text-sm leading-relaxed">
                                                Draft a counter-clause for section 3.1 regarding the personal liability cap.
                                            </p>
                                        </div>
                                    </div>

                                    {/* AI Message with Code/Quote */}
                                    <div className="flex justify-start">
                                        <div className="bg-white rounded-2xl rounded-tl-sm p-5 shadow-sm border border-gray-100 max-w-[90%]">
                                            <p className="text-sm text-gray-800 mb-4">
                                                Here is a suggested redline that limits liability to cases of proven fraud, excluding gross negligence:
                                            </p>
                                            <div className="bg-[#f1f5f9] rounded-lg p-4 border-l-4 border-[#166534] font-mono text-xs text-gray-700 leading-relaxed">
                                                "3.1. Liability shall be limited to instances of proven willful misconduct or fraud. Gross negligence shall not constitute grounds for personal financial recovery..."
                                            </div>
                                            <div className="flex gap-2 mt-4">
                                                <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors">
                                                    <div className="w-3.5 h-3.5"><Copy className="w-full h-full" /></div>
                                                    Copy
                                                </button>
                                                <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors">
                                                    <div className="w-3.5 h-3.5"><CornerDownLeft className="w-full h-full" /></div>
                                                    Insert to Doc
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Input Area */}
                                <div className="p-4 bg-white border-t border-gray-100">
                                    <div className="relative">
                                        <input
                                            type="text"
                                            placeholder="Ask Overide to refine or explain..."
                                            className="w-full bg-white border border-gray-200 rounded-full pl-6 pr-14 py-4 text-sm focus:outline-none focus:border-[#166534] focus:ring-1 focus:ring-[#166534] shadow-sm transition-all"
                                        />
                                        <button className="absolute right-3 top-1/2 -translate-y-1/2 w-9 h-9 bg-[#166534] hover:bg-[#14532d] rounded-full flex items-center justify-center text-white transition-colors shadow-md">
                                            <span className="sr-only">Send</span>
                                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" /></svg>
                                        </button>
                                    </div>
                                    <div className="flex justify-center gap-3 mt-4">
                                        <button className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-lg transition-colors font-medium">
                                            Suggest Redlines
                                        </button>
                                        <button className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-lg transition-colors font-medium">
                                            Explain Risks
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>


            </section>
        </div>
    );
}

export default Split;