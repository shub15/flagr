import React, { useState } from 'react';
import { UploadCloud, FileText, X, ArrowRight, Sparkles, Info } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

function Upload() {
    const [currentStep, setCurrentStep] = useState(1);
    const [purpose, setPurpose] = useState('review');
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);
    const [context, setContext] = useState('');
    const [error, setError] = useState<string | null>(null);

    const purposeOptions = [
        {
            id: 'company',
            label: 'Contracts',
            tooltip: 'For NOCs, HR policies, internal guidelines, letters, etc.'
        },
        {
            id: 'agreement',
            label: 'Agreements',
            tooltip: 'For contracts between individuals, companies, or both.'
        },
        {
            id: 'privacy',
            label: 'Privacy',
            tooltip: 'For privacy policies, data policies, terms, compliance docs.'
        },
        {
            id: 'legal',
            label: 'Legal',
            tooltip: 'For notices, legal disputes, applications, filings, case documents.'
        }
    ];

    const goToStep = (step: number) => {
        setCurrentStep(step);
    };

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            const file = files[0];
            // Validate file type
            if (file.type !== 'application/pdf') {
                setError('Please upload a PDF file only');
                return;
            }
            // Validate file size (max 10MB)
            if (file.size > 10 * 1024 * 1024) {
                setError('File size must be less than 10MB');
                return;
            }
            setUploadedFile(file);
            setError(null);
        }
    };

    const removeFile = () => {
        setUploadedFile(null);
    };

    const navigate = useNavigate();

    const handleGenerateReview = () => {
        if (!uploadedFile) {
            setError('Please upload a PDF file first');
            return;
        }

        // Navigate to split route immediately with file data
        navigate('/split', {
            state: {
                file: uploadedFile,
                purpose,
                context: context.trim()
            }
        });
    };

    return (
        <div className="min-h-screen relative overflow-hidden flex flex-col items-center justify-center">
            {/* Background Elements (Consistent with Landing Page) */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-[#dcedf0] via-[#eef6f6] to-[#d8f0e9]"></div>
                <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-purple-200/30 rounded-full mix-blend-multiply filter blur-[80px] animate-pulse"></div>
                <div className="absolute bottom-[10%] right-[-5%] w-[600px] h-[600px] bg-teal-200/30 rounded-full mix-blend-multiply filter blur-[80px]"></div>
            </div>

            {/* Navigation (Minimal) */}
            <nav className="absolute top-8 z-20 animate-slide-in">
                <a href="/" className="text-gray-900 font-serif-italic text-xl tracking-wide">
                    Overrule
                </a>
            </nav>

            {/* Main Card */}
            <main className="relative z-10 w-full max-w-lg px-4">
                <div className="glass-panel rounded-[32px] p-8 md:p-10 animate-slide-in">
                    {/* Progress Indicator */}
                    <div className="flex items-center gap-2 mb-8">
                        <div
                            className={`h-1 flex-1 rounded-full transition-all duration-300 ${currentStep >= 1 ? 'bg-black' : 'bg-gray-200'
                                }`}
                        ></div>
                        <div
                            className={`h-1 flex-1 rounded-full transition-all duration-300 ${currentStep >= 2 ? 'bg-black' : 'bg-gray-200'
                                }`}
                        ></div>
                    </div>

                    {/* STEP 1: UPLOAD */}
                    <div
                        className={`space-y-6 transition-all duration-400 ${currentStep === 1 ? 'block' : 'hidden-step'
                            }`}
                        style={{
                            opacity: currentStep === 1 ? 1 : 0,
                            transform: currentStep === 1 ? 'translateX(0)' : 'translateX(-20px)'
                        }}
                    >
                        <div className="text-center mb-6">
                            <h1 className="font-serif text-3xl text-gray-900">Upload document</h1>
                            <p className="text-sm text-gray-500 font-light mt-1">Select the purpose and add your files.</p>
                        </div>

                        {/* 1. Purpose Selector */}
                        <div>
                            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 block">
                                Purpose
                            </label>
                            <div className="grid grid-cols-2 gap-3">
                                {purposeOptions.map((option) => (
                                    <div key={option.id} className="relative group">
                                        <label className="cursor-pointer block">
                                            <input
                                                type="radio"
                                                name="purpose"
                                                className="peer sr-only"
                                                checked={purpose === option.id}
                                                onChange={() => setPurpose(option.id)}
                                            />
                                            <div className="px-4 py-3 rounded-xl border border-transparent bg-white/50 text-center text-sm text-gray-600 peer-checked:bg-white peer-checked:border-gray-200 peer-checked:text-black peer-checked:shadow-sm transition-all hover:bg-white/40">
                                                <div className="flex items-center justify-center gap-2">
                                                    <span>{option.label}</span>
                                                    {option.tooltip && (
                                                        <Info className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                                                    )}
                                                </div>
                                            </div>
                                        </label>
                                        {option.tooltip && (
                                            <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs rounded-lg py-2 px-3 whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
                                                {option.tooltip}
                                                <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* 2. Upload Area */}
                        <div className="relative group">
                            <input
                                type="file"
                                id="file-upload"
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                                onChange={handleFileUpload}
                                accept=".pdf,application/pdf"
                            />
                            <div className="border-2 border-dashed border-gray-300 rounded-2xl p-8 flex flex-col items-center justify-center text-center bg-white/30 transition-colors group-hover:bg-white/50 group-hover:border-gray-400">
                                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-sm mb-3">
                                    <UploadCloud className="w-5 h-5 text-gray-600" />
                                </div>
                                <p className="text-sm font-medium text-gray-800">Click to upload or drag & drop</p>
                                <p className="text-xs text-gray-400 mt-1">PDF only (Max 10MB)</p>
                            </div>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-600">
                                {error}
                            </div>
                        )}

                        {/* Uploaded File */}
                        {uploadedFile && (
                            <div className="bg-white/60 rounded-xl p-3 flex items-center gap-3 border border-white">
                                <div className="w-8 h-8 bg-red-50 rounded-lg flex items-center justify-center text-red-500">
                                    <FileText className="w-4 h-4" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-gray-800 truncate">
                                        {uploadedFile.name}
                                    </p>
                                    <p className="text-[10px] text-gray-400">
                                        {(uploadedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready
                                    </p>
                                </div>
                                <button
                                    className="text-gray-400 hover:text-red-500 transition-colors"
                                    onClick={removeFile}
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        )}

                        {/* Next Button */}
                        <button
                            onClick={() => goToStep(2)}
                            disabled={!uploadedFile}
                            className="w-full bg-black text-white py-3.5 rounded-xl font-medium text-sm mt-4 hover:bg-gray-800 hover:scale-[1.01] transition-all shadow-lg shadow-gray-400/20 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                        >
                            Next Step <ArrowRight className="w-4 h-4" />
                        </button>
                    </div>

                    {/* STEP 2: CONTEXT */}
                    <div
                        className={`space-y-6 transition-all duration-400 ${currentStep === 2 ? 'block' : 'hidden-step'
                            }`}
                        style={{
                            opacity: currentStep === 2 ? 1 : 0,
                            transform: currentStep === 2 ? 'translateX(0)' : 'translateX(20px)'
                        }}
                    >
                        {/* Header */}
                        <div className="text-center mb-6">
                            <h1 className="font-serif text-3xl text-gray-900">Add context</h1>
                            <p className="text-sm text-gray-500 font-light mt-1">Help the AI understand your position.</p>
                        </div>

                        {/* Text Area */}
                        <div className="space-y-2">
                            <textarea
                                className="glass-input w-full rounded-2xl p-4 text-sm text-gray-800 placeholder-gray-400 min-h-[160px] resize-none"
                                placeholder="E.g., I am the freelancer in this agreement. I want to ensure I retain IP rights for my work and that payment terms are net-30..."
                                value={context}
                                onChange={(e) => setContext(e.target.value)}
                            ></textarea>

                            {/* Tip Box */}
                            <div className="flex gap-2 items-start px-1">
                                <Sparkles className="w-3.5 h-3.5 text-gray-400 mt-0.5 flex-shrink-0" />
                                <p className="text-xs text-gray-400 font-light leading-relaxed">
                                    Mention your side (e.g., Buyer/Seller), your priorities, and how this contract influences your
                                    business or life goals.
                                </p>
                            </div>

                            {/* Error Message */}
                            {error && (
                                <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-600">
                                    {error}
                                </div>
                            )}
                        </div>

                        {/* Actions */}
                        <div className="flex flex-col gap-3 pt-2">
                            <button
                                onClick={handleGenerateReview}
                                disabled={!uploadedFile}
                                className="w-full bg-black text-white py-3.5 rounded-xl font-medium text-sm hover:bg-gray-800 hover:scale-[1.01] transition-all shadow-lg shadow-gray-400/20 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                            >
                                Generate Review
                            </button>
                            <button
                                onClick={() => goToStep(1)}
                                className="w-full text-gray-500 py-2 text-xs font-medium hover:text-black transition-colors"
                            >
                                Back to upload
                            </button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default Upload;
