import React, { useState, useRef } from 'react';
import { Copy, Download, RefreshCcw, Send, Bell, Mail, FileText, File } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import html2pdf from 'html2pdf.js';

import { deliverPush, deliverEmail } from '../services/api';

const ReportView = ({ 
  topic, 
  report, 
  variants, 
  comparisonData,
  onSelectVariant, 
  onAcceptRefinement,
  onDiscardRefinement,
  onReset, 
  onRefine, 
  isRefining, 
  sessionId, 
  userEmail 
}) => {
  const [feedback, setFeedback] = useState('');
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);
  const reportRef = useRef(null);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(report);
  };

  const downloadPDF = () => {
    if (!reportRef.current) return;
    const opt = {
      margin: 10,
      filename: `${topic.replace(/\s+/g, '_')}_research.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
      pagebreak: { mode: 'avoid-all' }
    };
    html2pdf().from(reportRef.current).set(opt).save();
  };

  const downloadDOCX = () => {
    if (!reportRef.current) return;
    const html = reportRef.current.innerHTML;
    const preHtml = `<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'><head><meta charset='utf-8'><title>Export HTML To Doc</title></head><body>`;
    const postHtml = "</body></html>";
    const blob = new Blob(['\ufeff', preHtml + html + postHtml], {
      type: 'application/msword'
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${topic.replace(/\s+/g, '_')}_research.doc`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleRefineSubmit = (e) => {
    e.preventDefault();
    if (feedback.trim()) {
      onRefine(feedback);
      setFeedback('');
    }
  };

  // Comparison View Mode
  if (comparisonData) {
    const panels = [
      { 
        title: "Previous Version", 
        content: comparisonData.previous, 
        type: "old",
        action: { label: "Keep Original", onClick: onDiscardRefinement, style: "bg-ink text-white hover:bg-black uppercase tracking-widest font-bold" }
      },
      { 
        title: "Updated Version", 
        content: comparisonData.updated, 
        type: "new",
        action: { label: "Accept Changes", onClick: () => onAcceptRefinement(comparisonData.updated), style: "bg-ink text-white hover:bg-black" }
      }
    ];

    return (
      <div className="max-w-[1400px] mx-auto px-6 pb-56">
        <div className="mb-12 text-center pt-8">
          <h2 className="text-2xl font-bold text-ink tracking-tight">Review Refinements</h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          {panels.map((panel, index) => (
            <div
              key={index}
              className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm flex flex-col h-[800px]"
            >
              <div className="px-8 py-6 bg-white border-b border-gray-50 flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <div className={`w-2 h-2 rounded-full ${panel.type === 'old' ? 'bg-gray-300' : 'bg-green-500'}`} />
                    <h3 className="text-[10px] font-bold uppercase text-gray-400">
                      {panel.title}
                    </h3>
                  </div>
                  <p className="text-lg font-semibold text-ink">{panel.type === 'old' ? 'Before' : 'After'}</p>
                </div>
                <button
                  onClick={panel.action.onClick}
                  className={`px-6 py-2.5 border rounded-full text-xs font-bold uppercase tracking-widest transition-all hover:scale-[1.05] active:scale-[0.95] ${panel.action.style}`}
                >
                  {panel.action.label}
                </button>
              </div>

              <div className="p-10 prose prose-slate max-w-none prose-headings:font-semibold prose-sm overflow-y-auto flex-grow custom-scrollbar">
                <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                  {panel.content}
                </ReactMarkdown>
              </div>
            </div>
          ))}
        </div>

        <div className="fixed bottom-0 left-0 w-full z-20">
          <div className="bg-gradient-to-t from-paper via-paper to-transparent pt-12 pb-8 px-4">
            <div className="max-w-3xl mx-auto">
              <div className="bg-white border border-gray-100 rounded-2xl shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.08)] p-2">
                <form onSubmit={handleRefineSubmit} className="relative flex items-end">
                  <textarea
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Refine further if needed..."
                    className="w-full min-h-[56px] max-h-32 p-4 bg-transparent border-none focus:ring-0 focus:outline-none transition-all resize-none text-sm pr-14 custom-scrollbar"
                    rows={1}
                    onInput={(e) => {
                      e.target.style.height = 'auto';
                      e.target.style.height = e.target.scrollHeight + 'px';
                    }}
                    disabled={isRefining}
                  />
                  <button
                    type="submit"
                    disabled={isRefining || !feedback.trim()}
                    className="absolute bottom-2 right-2 p-3 bg-ink text-white rounded-xl hover:bg-black disabled:bg-gray-100 disabled:text-gray-400 transition-all active:scale-95"
                  >
                    <Send size={18} />
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (variants && variants.length > 0) {
    return (
      <div className="max-w-[1400px] mx-auto px-6 pb-56">
        <div className="mb-12 text-center pt-8">
          <h2 className="text-2xl font-bold text-ink tracking-tight">Select Refined Version</h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          {variants.map((variant, index) => (
            <div
              key={index}
              className="bg-white border border-gray-100 rounded-2xl overflow-hidden hover:shadow-[0_8px_30px_-4px_rgba(0,0,0,0.08)] flex flex-col h-[800px]"
            >
              <div className="px-8 py-6 bg-white border-b border-gray-50 flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <div className={`w-2 h-2 rounded-full ${index === 0 ? 'bg-blue-500' : 'bg-purple-500'}`} />
                    <h3 className="text-[10px] font-bold uppercase text-gray-400">
                      {variant.type} Perspective
                    </h3>
                  </div>
                  <p className="text-lg font-semibold text-ink capitalize">{variant.type} Version</p>
                </div>
                <button
                  onClick={() => onSelectVariant(variant.content)}
                  className="px-6 py-2.5 bg-ink text-white text-xs font-bold uppercase tracking-widest rounded-full hover:bg-black transition-all hover:scale-[1.05] active:scale-[0.95] shadow-lg shadow-gray-200"
                >
                  Select This
                </button>
              </div>

              <div className="p-10 prose prose-slate max-w-none prose-headings:font-semibold prose-sm overflow-y-auto flex-grow custom-scrollbar">
                <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                  {variant.content}
                </ReactMarkdown>
              </div>
            </div>
          ))}
        </div>

        {/* Static Refinement Box for Variants */}
        <div className="fixed bottom-0 left-0 w-full z-20">
          <div className="bg-gradient-to-t from-paper via-paper to-transparent pt-12 pb-8 px-4">
            <div className="max-w-3xl mx-auto">
              <div className="bg-white border border-gray-100 rounded-2xl shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.08)] p-2">
                <form onSubmit={handleRefineSubmit} className="relative flex items-end">
                  <textarea
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Refine these versions further..."
                    className="w-full min-h-[56px] max-h-32 p-4 bg-transparent border-none focus:ring-0 focus:outline-none transition-all resize-none text-sm pr-14 custom-scrollbar"
                    rows={1}
                    onInput={(e) => {
                      e.target.style.height = 'auto';
                      e.target.style.height = e.target.scrollHeight + 'px';
                    }}
                    disabled={isRefining}
                  />
                  <button
                    type="submit"
                    disabled={isRefining || !feedback.trim()}
                    className="absolute bottom-2 right-2 p-3 bg-ink text-white rounded-xl hover:bg-black disabled:bg-gray-100 disabled:text-gray-400 transition-all active:scale-95"
                  >
                    <Send size={18} />
                  </button>
                </form>
              </div>

            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 pb-56">
      <div className="flex items-center justify-between mb-12 border-b border-gray-100 pb-8">
        <div>
          <h1 className="text-3xl font-semibold mt-2">{topic}</h1>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={copyToClipboard}
            className="p-2 text-gray-400 hover:text-ink transition-colors"
            title="Copy to clipboard"
          >
            <Copy size={18} />
          </button>

          <div className="relative">
            <button
              onClick={() => setShowDownloadMenu(!showDownloadMenu)}
              className="p-2 text-gray-400 hover:text-ink transition-colors"
              title="Download Report"
            >
              <Download size={18} />
            </button>
            {showDownloadMenu && (
              <div className="absolute right-0 mt-2 w-32 bg-white border border-gray-100 rounded-md shadow-lg z-20">
                <button
                  onClick={() => { downloadPDF(); setShowDownloadMenu(false); }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center"
                >
                  <FileText size={14} className="mr-2" /> PDF
                </button>
                <button
                  onClick={() => { downloadDOCX(); setShowDownloadMenu(false); }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center"
                >
                  <File size={14} className="mr-2" /> DOCX
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mb-16" ref={reportRef}>
        <div className="prose prose-sm sm:prose-base prose-slate max-w-none prose-headings:font-semibold prose-a:text-blue-600">
          <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
            {report}
          </ReactMarkdown>
        </div>
      </div>

      {/* Static Refinement Box */}
      <div className="fixed bottom-0 left-0 w-full z-20">
        <div className="bg-gradient-to-t from-paper via-paper to-transparent pt-12 pb-8 px-4">
          <div className="max-w-3xl mx-auto">
            <div className="bg-white border border-gray-100 rounded-2xl shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.08)] p-2">
              <form onSubmit={handleRefineSubmit} className="relative flex items-end">
                <textarea
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="Ask for changes or refinements..."
                  className="w-full min-h-[56px] max-h-32 p-4 bg-transparent border-none focus:ring-0 focus:outline-none transition-all resize-none text-sm pr-14 custom-scrollbar"
                  rows={1}
                  onInput={(e) => {
                    e.target.style.height = 'auto';
                    e.target.style.height = e.target.scrollHeight + 'px';
                  }}
                  disabled={isRefining}
                />
                <button
                  type="submit"
                  disabled={isRefining || !feedback.trim()}
                  className="absolute bottom-2 right-2 p-3 bg-ink text-white rounded-xl hover:bg-black disabled:bg-gray-100 disabled:text-gray-400 transition-all active:scale-95"
                >
                  <Send size={18} />
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportView;
