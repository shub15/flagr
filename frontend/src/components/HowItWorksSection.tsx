import React from 'react';
import { Lock, Trash2, UserCheck } from 'lucide-react';

const HowItWorksSection: React.FC = () => {
    const steps = [
        {
            number: 1,
            title: 'Upload',
            description: 'PDF, DOCX, or clear image scans.',
            active: true,
        },
        {
            number: 2,
            title: 'Add context',
            description: 'Define your role, jurisdiction, and priorities.',
            active: false,
        },
        {
            number: 3,
            title: 'Review',
            description: 'Get risks, negotiables, and suggested edits.',
            active: false,
        },
    ];

    const securityFeatures = [
        {
            icon: Lock,
            text: 'Encrypted in transit and at rest.',
        },
        {
            icon: Trash2,
            text: 'No retention by default; delete with one click.',
        },
        {
            icon: UserCheck,
            text: '"Not legal advice." You stay in control.',
        },
    ];

    return (
        <section className="w-full pb-24 animate-fade-up delay-500">
            <div className="glass-panel rounded-[40px] p-8 md:p-12">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
                    {/* How it Works */}
                    <div>
                        <h2 className="font-georgia text-3xl font-normal mb-8">How it works</h2>
                        <div className="space-y-8">
                            {steps.map((step) => (
                                <div key={step.number} className="flex gap-4 items-start">
                                    <span
                                        className={`flex-shrink-0 w-6 h-6 rounded-full text-xs flex items-center justify-center mt-1 ${step.active
                                            ? 'bg-black text-white'
                                            : 'bg-white border border-gray-200 text-gray-500'
                                            }`}
                                    >
                                        {step.number}
                                    </span>
                                    <div>
                                        <h4 className="font-medium text-gray-900">{step.title}</h4>
                                        <p className="text-sm text-gray-500 font-light mt-1">
                                            {step.description}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Security (Visual Box) */}
                    <div
                        id="security"
                        className="bg-white/40 rounded-3xl p-8 border border-white/60 relative overflow-hidden"
                    >
                        <div className="absolute -top-10 -right-10 w-32 h-32 bg-green-100/50 rounded-full blur-xl"></div>

                        <div className="relative z-10">
                            <h2 className="font-georgia text-3xl font-normal mb-6">Private by default.</h2>
                            <ul className="space-y-4">
                                {securityFeatures.map((feature, index) => {
                                    const Icon = feature.icon;
                                    return (
                                        <li
                                            key={index}
                                            className="flex items-center gap-3 text-sm text-gray-600 font-light"
                                        >
                                            <Icon className="w-4 h-4 text-gray-400" />
                                            {feature.text}
                                        </li>
                                    );
                                })}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default HowItWorksSection;
