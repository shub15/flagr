import React from 'react';
import { Users, ScanText, PenLine } from 'lucide-react';

const FeaturesGrid: React.FC = () => {
    const features = [
        {
            icon: Users,
            title: 'Council of experts',
            description:
                'Multiple specialized models analyze risk, compliance, finance, and drafting simultaneously.',
        },
        {
            icon: ScanText,
            title: 'Clause‑level citations',
            description:
                'Every claim links to exact text spans within your document—no black box opinions.',
        },
        {
            icon: PenLine,
            title: 'Redline suggestions',
            description:
                'Ready‑to‑paste language for negotiation emails or direct policy updates.',
        },
    ];

    return (
        <section id="features" className="w-full pb-24 animate-fade-up delay-400">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {features.map((feature, index) => {
                    const Icon = feature.icon;
                    return (
                        <div
                            key={index}
                            className="glass-panel p-8 rounded-3xl hover:bg-white/50 transition-colors duration-300"
                        >
                            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center mb-6 shadow-sm border border-gray-100">
                                <Icon className="w-5 h-5 text-gray-700" />
                            </div>
                            <h3 className="font-georgia text-2xl font-normal mb-3 text-gray-900">{feature.title}</h3>
                            <p className="text-gray-500 font-light leading-relaxed text-sm">
                                {feature.description}
                            </p>
                        </div>
                    );
                })}
            </div>
        </section>
    );
};

export default FeaturesGrid;
