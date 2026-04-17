import React, { useState, useEffect } from 'react';

const STATUS_MAP = {
  starting: { text: 'Processing input', icon: '⚡' },
  discovery_complete: { text: 'Searching the web using Serper Tool', icon: '🔎' },
  urls_selected: { text: 'Fetching data using Playwright', icon: '📡' },
  scraping: { text: 'Analyzing sources using CrewAI', icon: '🔬' },
  aggregated: { text: 'Summarizing data using LLM - OpenAI', icon: '📊' },
  report_generated: { text: 'Drafting report using LLM - OpenAI', icon: '✍️' },
  completed: { text: 'Finalizing output using AutoGen Refiner', icon: '✨' },
};

const LoadingStatus = ({ status }) => {
  const [current, setCurrent] = useState(STATUS_MAP['starting']);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    let nextStatus;
    if (typeof status === 'object' && status !== null) {
      nextStatus = {
        text: status.message || 'Processing',
        icon: status.variant === 'A' ? '🧐' : status.variant === 'B' ? '🫡' : '🤔'
      };
    } else {
      nextStatus = STATUS_MAP[status] || { text: status, icon: '🤔' };
    }

    if (nextStatus.text !== current.text) {
      setIsExiting(true);
      const timer = setTimeout(() => {
        setCurrent(nextStatus);
        setIsExiting(false);
      }, 400);
      return () => clearTimeout(timer);
    }
  }, [status, current.text]);

  return (
    <div className="flex flex-col items-center justify-center py-32 px-4">
      {/* Animated Pulse Ring */}
      <div className="relative mb-12">
        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
          <span className="text-2xl">{current.icon}</span>
        </div>
        <div className="absolute inset-0 w-16 h-16 rounded-full border-2 border-gray-200 animate-ping opacity-30" />
        <div
          className="absolute inset-0 w-16 h-16 rounded-full border border-gray-300 animate-pulse"
          style={{ animationDuration: '2s' }}
        />
      </div>

      {/* Transitioning Text */}
      <div className="h-8 flex items-center justify-center overflow-hidden">
        <p
          className={`text-lg font-medium text-gray-500 tracking-wide transition-all duration-400 ${isExiting
            ? 'opacity-0 translate-y-3'
            : 'opacity-100 translate-y-0'
            }`}
        >
          {current.text}
          <span className="inline-flex ml-1">
            <DotAnimation />
          </span>
        </p>
      </div>

      {/* Subtle Progress Bar */}
      <div className="mt-8 w-48 h-0.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-gray-300 rounded-full"
          style={{
            animation: 'progressSlide 3s ease-in-out infinite',
          }}
        />
      </div>

      <p className="mt-6 text-xs text-gray-300 tracking-widest uppercase">
        This may take a minute
      </p>

      <style>{`
        @keyframes progressSlide {
          0% { width: 0%; margin-left: 0%; }
          50% { width: 60%; margin-left: 20%; }
          100% { width: 0%; margin-left: 100%; }
        }
      `}</style>
    </div>
  );
};

/** Animated typing dots */
const DotAnimation = () => {
  const [dots, setDots] = useState('');

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? '' : prev + '.'));
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return <span className="font-mono text-gray-400 w-4 inline-block">{dots}</span>;
};

export default LoadingStatus;
