import React from 'react';
import { Info, Check, Download } from 'lucide-react';

interface RefineTabProps {
    onDownload?: () => void;
}

interface Suggestion {
    id: string;
    quoteNo: string;
    title: string;
    original: string;
    correction: string;
    type: string;
}

const DUMMY_SUGGESTIONS: Suggestion[] = [
    {
        id: '1',
        quoteNo: '001',
        title: 'Correct the capitalization',
        original: 'iwas',
        correction: 'I was',
        type: 'Capitalization'
    },
    {
        id: '2',
        quoteNo: '002',
        title: 'Grammar: Subject-Verb Agreement',
        original: 'The terms is',
        correction: 'The terms are',
        type: 'Grammar'
    },
    {
        id: '3',
        quoteNo: '003',
        title: 'Word Choice: Legal Clarity',
        original: 'Parties hereto agreeable',
        correction: 'Parties hereto agree',
        type: 'Word Choice'
    }
];

export default function RefineTab({ onDownload }: RefineTabProps) {
    return (
        <div className="flex-1 overflow-y-auto custom-scroll p-6 bg-[#f8f9fa]">
            <div className="mb-8 flex justify-between items-start">
                <div>
                    <h2 className="font-serif text-3xl text-black mb-2">Suggested Improvements</h2>
                    <p className="text-gray-500 text-sm">Review and accept changes to refine your contract.</p>
                </div>
                {onDownload && (
                    <button
                        onClick={onDownload}
                        className="flex items-center gap-2 bg-[#0C4522] text-white px-5 py-2.5 rounded-xl hover:bg-[#0a3f1f] transition-all shadow-sm"
                    >
                        <Download className="w-4 h-4" />
                        Download
                    </button>
                )}
            </div>

            <div className="space-y-4">
                {DUMMY_SUGGESTIONS.map((suggestion) => (
                    <div key={suggestion.id} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${suggestion.type === 'Capitalization' ? 'bg-red-500' :
                                    suggestion.type === 'Grammar' ? 'bg-orange-500' : 'bg-blue-500'
                                    }`}></div>
                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                                    QUOTE NO. {suggestion.quoteNo}
                                </span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="font-semibold text-gray-900">{suggestion.title}</span>
                                <Info className="w-4 h-4 text-gray-400" />
                            </div>
                        </div>

                        <div className="mb-6 space-y-2 font-mono text-sm">
                            <div className="flex gap-2">
                                <span className="text-gray-400 line-through decoration-red-400 decoration-2">{suggestion.original}</span>
                                <span className="text-green-600 font-medium">{suggestion.correction}</span>
                                <span className="text-gray-600">about</span>
                            </div>
                            <div className="flex gap-2 text-gray-400 text-xs">
                                <span className="text-red-400 line-through">{suggestion.original}</span>
                                <span>{suggestion.original.replace(suggestion.original, suggestion.correction)} about to find out</span>
                            </div>
                        </div>

                        <div className="flex items-center gap-4">
                            <button className="flex items-center gap-2 bg-[#166534] text-white px-4 py-2 rounded-full text-sm font-medium hover:bg-[#14532d] transition-colors">
                                <Check className="w-4 h-4" />
                                Accept
                            </button>
                            <button className="text-gray-500 text-sm font-medium hover:text-gray-700">
                                Ignore
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
