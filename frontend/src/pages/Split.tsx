import React, { useState, useEffect } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import {
    Check,
    ShieldAlert,
    Coins,
    Plus,
    Info,
    Sparkles,
    CornerDownLeft,
    Share2,
    ThumbsUp,
    ThumbsDown,
    Globe,
    Lightbulb,
    Mic,
    Square,
    X,
    ChevronDown,
    ChevronUp,
    Download,
} from 'lucide-react';

import api from '../services/api';
import { config } from '../config';

interface Step {
    label: string;
    status: 'complete' | 'active' | 'pending';
    detail?: string;
}

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    quotes?: Array<{ text: string; confidence: number }>;
    suggestions?: string[];
    searchResults?: Array<{ title: string; link: string; snippet: string; source: string; date?: string }>;
}

interface LLMResponse {
    provider: string;
    model: string;
    raw_response: string;
    findings: any[];
    confidence: number;
    response_time_ms: number;
}

interface AgentCouncilResponse {
    agent_name: string;
    llm_responses: LLMResponse[];
    summary: string;
    total_findings: number;
    final_findings: number;
}

interface CouncilTransparencyResponse {
    review_id: string;
    agents: AgentCouncilResponse[];
}

const RefinementCard = ({ change }: { change: RefinementChange }) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
            {/* Header */}
            <div className="p-4 border-b border-gray-50 flex items-center justify-between bg-gray-50/50">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold tracking-wide 
                    ${change.category === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                        change.category === 'MISSING' ? 'bg-purple-100 text-purple-700' :
                            change.category === 'NEGOTIABLE' ? 'bg-amber-100 text-amber-700' :
                                'bg-gray-100 text-gray-700'}`}>
                    {change.category}
                </span>
                <div className="flex gap-2">
                    <button className="text-xs font-medium text-green-700 hover:bg-green-50 px-3 py-1.5 rounded-lg border border-transparent hover:border-green-100 transition-colors">
                        Accept
                    </button>
                    <button className="text-xs font-medium text-gray-500 hover:bg-gray-100 px-3 py-1.5 rounded-lg transition-colors">
                        Reject
                    </button>
                </div>
            </div>

            <div className="p-5 flex flex-col gap-4">
                {/* Original or Missing */}
                <div className="space-y-2">
                    <h4 className="text-xs uppercase tracking-wider text-gray-400 font-semibold flex items-center gap-2">
                        {change.original_clause ? 'Original Clause' : 'Status'}
                    </h4>
                    {change.original_clause ? (
                        <div className="p-4 bg-red-50/30 rounded-lg text-sm text-gray-600 leading-relaxed border border-red-100/50 font-mono">
                            {change.original_clause}
                        </div>
                    ) : (
                        <div className="p-4 bg-gray-50 rounded-lg text-sm text-gray-500 italic border border-gray-100">
                            <span className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>
                                Missing Clause
                            </span>
                        </div>
                    )}
                </div>

                {/* Improved */}
                <div className="space-y-2">
                    <h4 className="text-xs uppercase tracking-wider text-green-600 font-semibold">
                        {change.category === 'MISSING' ? 'Proposed Addition' : 'Improved Version'}
                    </h4>
                    <div className="p-4 bg-green-50/30 rounded-lg text-sm text-gray-800 leading-relaxed border border-green-100/50 shadow-sm">
                        {change.improved_clause}
                    </div>
                </div>
            </div>

            {/* Accordion Reasoning */}
            <div className="border-t border-gray-100">
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="w-full flex items-center justify-between p-3 bg-gray-50/30 hover:bg-gray-50 transition-colors text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                    <span className="pl-2">Reasoning & Analysis</span>
                    {isOpen ? <ChevronUp className="w-4 h-4 mr-2" /> : <ChevronDown className="w-4 h-4 mr-2" />}
                </button>
                {isOpen && (
                    <div className="p-5 pt-2 bg-blue-50/10 text-sm text-gray-600 leading-relaxed border-t border-gray-100 animate-slide-in">
                        <div className="flex gap-3">
                            <div className="min-w-[4px] bg-blue-500/20 rounded-full my-1"></div>
                            <div>{change.reasoning}</div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

interface RefinementChange {
    change_id: string;
    category: 'CRITICAL' | 'MISSING' | 'NEGOTIABLE' | 'Standard';
    original_clause: string | null;
    improved_clause: string;
    reasoning: string;
    affected_issue: string;
}

interface RefinementData {
    review_id: string;
    total_changes: number;
    changes: RefinementChange[];
    summary: string;
    mode: string;
}

const SUGGESTED_BACKUPS = [
    "Explain this legal term in simple English",
    "Find latest past cases related to this",
    "Fetch latest news on this topic",
    "What are the risks here?",
    "Suggest a redline for this",
    "Is this standard market practice?"
];

function Split() {
    const location = useLocation();
    const { reviewId } = useParams<{ reviewId: string }>();
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

    // Review data from API
    const [reviewData, setReviewData] = useState<any>(null);
    const [activeTab, setActiveTab] = useState<'critical' | 'good' | 'missing' | 'negotiable'>('critical');

    const [rightPanelTab, setRightPanelTab] = useState<'analysis' | 'chat' | 'refine'>('analysis');
    const [showCorrectionInput, setShowCorrectionInput] = useState(false);

    const [correctionText, setCorrectionText] = useState('');


    // Translation State
    const [translation, setTranslation] = useState<{ text: string; lang: string } | null>(null);

    // Council Data State
    const [councilData, setCouncilData] = useState<CouncilTransparencyResponse | null>(null);
    const [isCouncilLoading, setIsCouncilLoading] = useState(false);
    const [translating, setTranslating] = useState(false);
    const [showLanguageDropdown, setShowLanguageDropdown] = useState(false);

    // Chat State
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [chatInput, setChatInput] = useState('');
    const [isChatLoading, setIsChatLoading] = useState(false);
    const [refinementData, setRefinementData] = useState<RefinementData | null>(null);
    const [isRefineLoading, setIsRefineLoading] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);

    // Removed incorrect placement of refine logic

    const messagesEndRef = React.useRef<HTMLDivElement>(null);

    // Voice State
    const [isRecording, setIsRecording] = useState(false);
    const [isVoiceMode, setIsVoiceMode] = useState(false);
    const [voiceStatus, setVoiceStatus] = useState("Idle"); // Idle, Listening, Processing, Speaking
    const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
    const [shouldPlayResponse, setShouldPlayResponse] = useState(false);


    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [chatMessages, isChatLoading]);


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

    useEffect(() => {
        if (rightPanelTab === 'refine' && currentReviewId && !refinementData) {
            fetchRefinements();
        }
    }, [rightPanelTab, currentReviewId]);

    const fetchRefinements = async () => {
        if (!currentReviewId) return;
        setIsRefineLoading(true);
        try {
            const res = await api.get(`/api/reviews/${currentReviewId}/refinement-preview`);
            setRefinementData(res.data);
        } catch (err) {
            console.error("Failed to fetch refinements", err);
        } finally {
            setIsRefineLoading(false);
        }
    };

    const handleRefineDownload = async () => {
        if (!currentReviewId) return;
        setIsDownloading(true);
        try {
            // First apply feedback/refinements
            await api.post(`/api/reviews/${currentReviewId}/refine-with-feedback`);

            // Then download the PDF
            window.open(`${config.apiBaseUrl}/api/reviews/${currentReviewId}/custom-refined-pdf`, '_blank');
        } catch (err) {
            console.error("Failed to download refined PDF", err);
            // Optionally show error toast here
        } finally {
            setIsDownloading(false);
        }
    };

    const handleShare = () => {
        if (!currentReviewId) {
            setApiError('No review id available for share');
            return;
        }
        const url = `${config.apiBaseUrl}/api/reviews/${currentReviewId}/annotated-pdf/redacted`;
        window.open(url, '_blank');
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

    const playAudioResponse = async (text: string) => {
        try {
            setVoiceStatus("Speaking");
            const res = await api.post('/api/voice/tts', { text }, { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const audio = new Audio(url);
            audio.onended = () => {
                setVoiceStatus("Idle");
                // If in voice mode, maybe restart listening automatically? For now, back to idle.
            };
            audio.play();
        } catch (err) {
            console.error("TTS Error", err);
            setVoiceStatus("Idle");
        }
    };

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream);
            const chunks: BlobPart[] = [];

            recorder.ondataavailable = (e) => chunks.push(e.data);
            recorder.onstop = async () => {
                const blob = new Blob(chunks, { type: 'audio/wav' });
                const formData = new FormData();
                formData.append('file', blob, 'recording.wav');

                // Stop tracks
                stream.getTracks().forEach(track => track.stop());

                setIsChatLoading(true);
                setVoiceStatus("Processing");
                try {
                    const res = await api.post('/api/voice/stt', formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    });
                    if (res.data.text) {
                        setChatInput(res.data.text);
                        // Auto-send and enable TTS
                        handleSendMessage(res.data.text, true);
                    } else {
                        setVoiceStatus("Idle");
                    }
                } catch (err) {
                    console.error("STT Error", err);
                    setVoiceStatus("Error");
                } finally {
                    setIsChatLoading(false);
                }
            };

            recorder.start();
            setMediaRecorder(recorder);
            setIsRecording(true);
            setVoiceStatus("Listening");

            // If we are in voice mode, we might want to auto start listening logic if needed, 
            // but simplified flow is: user clicks mic to speak.
        } catch (err) {
            console.error("Mic Error", err);
            alert("Could not access microphone");
            setVoiceStatus("Error");
        }
    };

    const stopRecording = () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            setIsRecording(false);
            setMediaRecorder(null);
        }
    };

    const toggleVoiceMode = () => {
        setIsVoiceMode(!isVoiceMode);
        if (!isVoiceMode) {
            // Entered Voice Mode
            setVoiceStatus("Idle");
        } else {
            // Exited Voice Mode
            stopRecording();
        }
    };

    const handleSendMessage = async (text?: string, fromVoice: boolean = false) => {
        const messageText = text || chatInput;
        if (!messageText.trim()) return;

        // Optimistic update
        setChatMessages(prev => [...prev, { role: 'user', content: messageText }]);
        setChatInput('');
        setIsChatLoading(true);

        try {
            let replyText = "";
            let newMsg: ChatMessage | null = null;

            if (messageText === "Fetch latest news on this topic" || messageText === "Find latest past cases related to this") {
                const query = messageText === "Fetch latest news on this topic" ? "latest law news" : "latest law cases";
                const response = await api.post('/api/search', {
                    query: query
                });

                if (response.data.organic) {
                    replyText = `Here are the latest ${messageText.includes("news") ? "news" : "cases"} I found:`;
                    newMsg = {
                        role: 'assistant',
                        content: replyText,
                        searchResults: response.data.organic,
                        suggestions: SUGGESTED_BACKUPS.slice(0, 3)
                    };
                } else {
                    replyText = "I couldn't find any relevant results at the moment.";
                    newMsg = {
                        role: 'assistant',
                        content: replyText,
                        suggestions: SUGGESTED_BACKUPS.slice(0, 3)
                    };
                }
            } else {
                if (!currentReviewId) throw new Error("No review ID");

                const response = await api.post(`/api/reviews/${currentReviewId}/ask`, {
                    question: messageText
                });

                // Select 3 random suggestions
                const shuffled = [...SUGGESTED_BACKUPS].sort(() => 0.5 - Math.random());
                const selectedSuggestions = shuffled.slice(0, 3);

                replyText = response.data.answer;
                newMsg = {
                    role: 'assistant',
                    content: replyText,
                    quotes: response.data.supporting_quotes,
                    suggestions: selectedSuggestions
                };
            }

            if (newMsg) {
                setChatMessages(prev => [...prev, newMsg!]);
                if (fromVoice || shouldPlayResponse) {
                    playAudioResponse(replyText);
                    setShouldPlayResponse(false);
                }
            }

        } catch (err: any) {
            console.error('Chat/Search failed:', err);
            const errText = "I'm sorry, I couldn't process that request. Please try again.";
            setChatMessages(prev => [...prev, {
                role: 'assistant',
                content: errText
            }]);
            if (fromVoice || shouldPlayResponse) {
                playAudioResponse(errText);
                setShouldPlayResponse(false);
            }
        } finally {
            setIsChatLoading(false);
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
                    setApiComplete(true);
                }
                return;
            }

            // Otherwise, create new review from uploaded file
            if (!file) {
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
                setApiComplete(true);
            }
        };

        makeApiCall();
    }, [reviewId, file, purpose, context, steps.length]);

    const fetchCouncilData = async (id: string) => {
        try {
            setIsCouncilLoading(true);
            const response = await api.get(`/api/reviews/${id}/council`);
            setCouncilData(response.data);
        } catch (err) {
            console.error("Failed to fetch council data:", err);
        } finally {
            setIsCouncilLoading(false);
        }
    };

    // Initial load for existing review
    useEffect(() => {
        if (reviewId) {
            fetchCouncilData(reviewId);
        }
    }, [reviewId]);

    // Fetch council data when new review is generated
    useEffect(() => {
        if (reviewData?.review_id) {
            fetchCouncilData(reviewData.review_id);
        }
    }, [reviewData?.review_id]);

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

    const getAgentStyle = (agentName: string) => {
        const name = agentName.toLowerCase();
        if (name.includes('risk') || name.includes('skeptic')) {
            return {
                label: 'Agent Risk',
                icon: <ShieldAlert className="w-3 h-3 text-[#BE123C]" />,
                colors: { bg: 'bg-[#FFF1F2]', border: 'border-[#FECDD3]', iconBg: 'bg-white', text: 'text-[#881337]', iconColor: 'text-[#9F1239]' }
            };
        } else if (name.includes('finance') || name.includes('auditor') || name.includes('compliance')) {
            return {
                label: 'Agent Compliance',
                icon: <Coins className="w-3 h-3 text-[#15803D]" />,
                colors: { bg: 'bg-[#F0FDF4]', border: 'border-[#BBF7D0]', iconBg: 'bg-white', text: 'text-[#14532D]', iconColor: 'text-[#15803D]' }
            };
        } else if (name.includes('strategy') || name.includes('strategist')) {
            return {
                label: 'Agent Strategy',
                icon: <Lightbulb className="w-3 h-3 text-[#1D4ED8]" />,
                colors: { bg: 'bg-[#EFF6FF]', border: 'border-[#BFDBFE]', iconBg: 'bg-white', text: 'text-[#1E3A8A]', iconColor: 'text-[#2563EB]' }
            };
        }
        // Default
        return {
            label: `Agent ${agentName.charAt(0).toUpperCase() + agentName.slice(1)}`,
            icon: <Info className="w-3 h-3 text-gray-500" />,
            colors: { bg: 'bg-gray-50', border: 'border-gray-200', iconBg: 'bg-white', text: 'text-gray-700', iconColor: 'text-gray-500' }
        };
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
                            {isVoiceMode ? (
                                <div className="flex-1 py-4 flex items-center justify-between px-6">
                                    <div className="flex items-center gap-2">
                                        <div className="live-indicator">
                                            <div className="pulsing-dot"></div>
                                            <span>LIVE VOICE</span>
                                        </div>
                                    </div>
                                    <button onClick={toggleVoiceMode} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                                        <X className="w-5 h-5 text-gray-500" />
                                    </button>
                                </div>
                            ) : (
                                <>
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
                                    <button
                                        onClick={() => setRightPanelTab('refine')}
                                        className={`flex-1 py-4 text-sm font-semibold transition-all relative ${rightPanelTab === 'refine'
                                            ? 'text-[#064E3B]'
                                            : 'text-gray-500 hover:text-gray-700'
                                            }`}
                                    >
                                        Refine
                                        {rightPanelTab === 'refine' && (
                                            <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#064E3B]"></div>
                                        )}
                                    </button>
                                </>
                            )}
                        </div>

                        {isVoiceMode ? (
                            <div className="flex-1 flex flex-col items-center justify-center relative p-6 bg-[radial-gradient(circle_at_center,#fff_0%,#f3f4f6_100%)]">
                                <div className="orb-container mb-12">
                                    {voiceStatus === "Speaking" && (
                                        <>
                                            <div className="speaking-wave" style={{ animationDelay: '0s' }}></div>
                                            <div className="speaking-wave" style={{ animationDelay: '0.6s' }}></div>
                                            <div className="speaking-wave" style={{ animationDelay: '1.2s' }}></div>
                                        </>
                                    )}
                                    <div className={`holographic-orb ${voiceStatus === "Speaking" ? "animate-pulse" : ""}`}></div>
                                    <div className="orb-glare"></div>
                                </div>

                                <div className="ai-status text-center z-10">
                                    <h2 className="font-serif text-3xl text-black mb-2">
                                        {voiceStatus === "Listening" ? "Listening..." :
                                            voiceStatus === "Processing" ? "Processing..." :
                                                voiceStatus === "Speaking" ? "Speaking..." : "I'm listening"}
                                    </h2>
                                    <p className="text-gray-400">
                                        {voiceStatus === "Listening" ? "Go ahead, I'm all ears." :
                                            voiceStatus === "Speaking" ? "Answering your question..." :
                                                "Tap the microphone to speak"}
                                    </p>
                                </div>

                                <div className="absolute bottom-10 flex gap-4">
                                    <button
                                        onClick={isRecording ? stopRecording : startRecording}
                                        className={`w-16 h-16 rounded-full flex items-center justify-center text-white transition-all shadow-lg hover:scale-105 active:scale-95 ${isRecording ? 'bg-red-500' : 'bg-black'}`}
                                    >
                                        {isRecording ? <Square className="w-6 h-6 fill-current" /> : <Mic className="w-8 h-8" />}
                                    </button>
                                </div>
                            </div>
                        ) : rightPanelTab === 'analysis' ? (
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
                                                        onClick={handleShare}
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
                                                    setCorrectionText('');
                                                }}
                                                className="flex-1 bg-[#166534] text-white text-2xl font-serif px-5 py-2.5 rounded-xl hover:bg-[#14532d] transition-all"
                                            >
                                                Correct agent
                                            </button>
                                            <button
                                                onClick={() => setRightPanelTab('refine')}
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

                                    {/* Agent 2: Finance */}
                                    {isCouncilLoading ? (
                                        <div className="text-center py-4 text-xs text-gray-400">Loading council insights...</div>
                                    ) : (
                                        councilData?.agents.map((agent, agentIdx) => {
                                            const style = getAgentStyle(agent.agent_name);
                                            return (
                                                <details key={agentIdx} className={`group ${style.colors.bg} border ${style.colors.border} rounded-xl`} open={agentIdx === 0}>
                                                    <summary className="flex items-center justify-between p-4 cursor-pointer list-none rounded-xl transition-colors">
                                                        <div className="flex items-center gap-3">
                                                            <div className={`w-6 h-6 rounded-full ${style.colors.iconBg} flex items-center justify-center border ${style.colors.border}`}>
                                                                {style.icon}
                                                            </div>
                                                            <span className={`text-xs font-semibold ${style.colors.text}`}>{style.label}</span>
                                                        </div>
                                                        <Plus className={`w-3 h-3 ${style.colors.iconColor} group-open:rotate-45 transition-transform`} />
                                                    </summary>
                                                    <div className="px-4 pb-4 pt-0">
                                                        <p className={`text-[11px] ${style.colors.text} leading-relaxed pl-9 whitespace-pre-wrap`}>
                                                            {agent.summary || "No specific summary provided."}
                                                        </p>
                                                        {agent.final_findings > 0 && (
                                                            <div className="pl-9 mt-2 hidden group-open:block">
                                                                <div className="text-[10px] opacity-70 mb-1 font-semibold uppercase">Findings count: {agent.final_findings}</div>
                                                            </div>
                                                        )}

                                                        {/* Raw Responses */}
                                                        <div className="pl-9 mt-4 space-y-4 hidden group-open:block">
                                                            {agent.llm_responses?.map((resp, idx) => (
                                                                <div key={idx} className="border-t border-black/5 pt-3">
                                                                    <div className="flex items-center gap-2 mb-2">
                                                                        <span className="text-[10px] font-bold uppercase tracking-wider opacity-60">{resp.model}</span>
                                                                        <span className="text-[9px] bg-black/5 px-1.5 py-0.5 rounded text-gray-500">{resp.provider}</span>
                                                                        <span className="text-[9px] text-gray-400">{resp.response_time_ms}ms</span>
                                                                    </div>
                                                                    <pre className="text-[10px] font-mono bg-white/50 p-3 rounded-lg border border-black/5 overflow-x-auto whitespace-pre-wrap text-gray-600">
                                                                        {resp.raw_response}
                                                                    </pre>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </details>
                                            );
                                        })
                                    )}
                                    {/* Fallback if no data and not loading */}
                                    {!isCouncilLoading && !councilData && (
                                        <div className="text-center py-4 text-xs text-gray-400">No council data available.</div>
                                    )}
                                </div>
                            </div>
                        ) : rightPanelTab === 'chat' ? (
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
                                    {chatMessages.length === 0 && (
                                        <div className="flex justify-start">
                                            <div className="bg-white rounded-2xl rounded-tl-sm p-5 shadow-sm border border-gray-100 max-w-[90%]">
                                                <p className="text-sm text-gray-800 leading-relaxed">
                                                    I've analyzed the <span className="font-semibold text-black">{reviewData?.contract_type || 'contract'}</span>.
                                                    {reviewData?.critical_points?.length > 0
                                                        ? ` There are ${reviewData.critical_points.length} critical risks.`
                                                        : ' The contract looks mostly safe.'}
                                                    How would you like to proceed?
                                                </p>
                                            </div>
                                        </div>
                                    )}

                                    {chatMessages.map((msg, idx) => (
                                        <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                            <div className={`${msg.role === 'user'
                                                ? 'bg-[#0f172a] text-white rounded-tr-sm'
                                                : 'bg-white text-gray-800 border border-gray-100 rounded-tl-sm'
                                                } rounded-2xl p-4 shadow-sm max-w-[90%]`}>

                                                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>

                                                {/* Search Results */}
                                                {msg.role === 'assistant' && msg.searchResults && (
                                                    <div className="mt-4 space-y-3">
                                                        {msg.searchResults.map((result, rIdx) => (
                                                            <a
                                                                key={rIdx}
                                                                href={result.link}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="block bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-xl p-3 transition-all group"
                                                            >
                                                                <div className="flex items-start justify-between gap-2">
                                                                    <h4 className="text-sm font-semibold text-blue-700 leading-snug group-hover:underline">
                                                                        {result.title}
                                                                    </h4>
                                                                    <CornerDownLeft className="w-3 h-3 text-gray-400 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                                                                </div>
                                                                <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                                                                    {result.snippet}
                                                                </p>
                                                                {result.date && (
                                                                    <span className="text-[10px] text-gray-400 mt-2 block">
                                                                        {result.date} • {result.source}
                                                                    </span>
                                                                )}
                                                            </a>
                                                        ))}
                                                    </div>
                                                )}

                                                {/* Quotes for assistant messages */}
                                                {msg.role === 'assistant' && msg.quotes && msg.quotes.length > 0 && (
                                                    <div className="mt-3 space-y-2">
                                                        {msg.quotes.map((quote, qIdx) => (
                                                            <div key={qIdx} className="bg-[#f1f5f9] rounded-lg p-3 border-l-4 border-[#166534] font-mono text-xs text-gray-700 leading-relaxed">
                                                                "{quote.text}"
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}

                                                {/* Suggestions */}
                                                {msg.role === 'assistant' && msg.suggestions && msg.suggestions.length > 0 && (
                                                    <div className="mt-4 flex flex-wrap gap-2">
                                                        {msg.suggestions.map((suggestion, sIdx) => (
                                                            <button
                                                                key={sIdx}
                                                                onClick={() => handleSendMessage(suggestion)}
                                                                className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-full text-xs text-gray-600 transition-colors"
                                                            >
                                                                <Lightbulb className="w-3 h-3 text-amber-500" />
                                                                {suggestion}
                                                            </button>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}

                                    {isChatLoading && (
                                        <div className="flex justify-start">
                                            <div className="bg-white rounded-2xl rounded-tl-sm p-4 shadow-sm border border-gray-100">
                                                <div className="flex gap-1">
                                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-75"></div>
                                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-150"></div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                    <div ref={messagesEndRef} />
                                </div>

                                {/* Input Area */}
                                <div className="p-4 bg-white border-t border-gray-100">
                                    <div className="relative">
                                        <input
                                            type="text"
                                            value={chatInput}
                                            onChange={(e) => setChatInput(e.target.value)}
                                            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                                            disabled={isChatLoading}
                                            placeholder="Ask Overrule to refine or explain..."
                                            className="w-full bg-white border border-gray-200 rounded-full pl-6 pr-14 py-4 text-sm focus:outline-none focus:border-[#166534] focus:ring-1 focus:ring-[#166534] shadow-sm transition-all"
                                        />
                                        <button
                                            onClick={() => handleSendMessage()}
                                            disabled={isChatLoading || !chatInput.trim()}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 w-9 h-9 bg-[#166534] hover:bg-[#14532d] disabled:bg-gray-300 rounded-full flex items-center justify-center text-white transition-colors shadow-md"
                                        >
                                            <span className="sr-only">Send</span>
                                            {isChatLoading ? (
                                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                            ) : (
                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" /></svg>
                                            )}
                                        </button>
                                        <button
                                            onClick={() => {
                                                toggleVoiceMode();
                                                setTimeout(() => startRecording(), 500); // Auto-start recording on enter? Maybe let user click.
                                            }}
                                            className={`absolute right-14 top-1/2 -translate-y-1/2 p-2 rounded-full transition-all text-gray-400 hover:text-gray-600 hover:bg-gray-100`}
                                            title="Switch to Voice Mode"
                                        >
                                            <Mic className="w-5 h-5" />
                                        </button>
                                    </div>
                                    <div className="flex justify-center gap-3 mt-4">
                                        <button
                                            onClick={() => handleSendMessage("Suggest redlines for critical issues")}
                                            className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-lg transition-colors font-medium"
                                        >
                                            Suggest Redlines
                                        </button>
                                        <button
                                            onClick={() => handleSendMessage("Explain the risks in this contract")}
                                            className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-lg transition-colors font-medium"
                                        >
                                            Explain Risks
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="flex-1 overflow-y-auto custom-scroll p-6">
                                {isRefineLoading ? (
                                    <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                                        <div className="w-8 h-8 border-2 border-green-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                                        <p>Generating refinements...</p>
                                    </div>
                                ) : refinementData ? (
                                    <div className="space-y-6">
                                        <div className="mb-6">
                                            <div className="flex justify-between items-start gap-4">
                                                <div>
                                                    <h3 className="font-serif text-2xl mb-2 text-gray-900">Contract Refinement</h3>

                                                </div>
                                                <button
                                                    onClick={handleRefineDownload}
                                                    disabled={isDownloading}
                                                    className="p-2.5 bg-green-700 hover:bg-green-800 disabled:bg-green-700/50 text-white rounded-lg transition-colors shrink-0 shadow-sm flex items-center justify-center min-w-[42px]"
                                                    title="Download Refined PDF"
                                                >
                                                    {isDownloading ? (
                                                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                                    ) : (
                                                        <Download className="w-5 h-5" />
                                                    )}
                                                </button>
                                            </div>
                                            <div className="mt-4 flex gap-4 text-sm font-medium text-gray-500 border-t border-gray-100 pt-4">
                                                <span>{refinementData.total_changes} Changes Proposed</span>
                                                <span>•</span>
                                                <span className="capitalize">{refinementData.mode} Mode</span>
                                            </div>
                                        </div>

                                        {refinementData.changes.map((change) => (
                                            <RefinementCard key={change.change_id} change={change} />
                                        ))}

                                        <div className="h-20 sm:hidden"></div>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                                        <p>No refinements available. Try analyzing a contract first.</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>


            </section>
        </div>
    );
}

export default Split;