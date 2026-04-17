import React, { useState, useEffect } from 'react';
import { RefreshCcw, Bell, Mail } from 'lucide-react';
import InputBox from './components/InputBox';
import ReportView from './components/ReportView';
import LoadingStatus from './components/LoadingStatus';
import Login from './components/Login';
import { requestResearchStream, refineResearch, deliverPush, deliverEmail, selectVariant } from './services/api';

const App = () => {
  const [sessionId, setSessionId] = useState(null);
  const [topic, setTopic] = useState('');
  const [report, setReport] = useState('');
  const [variants, setVariants] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefining, setIsRefining] = useState(false);
  const [refinementStatus, setRefinementStatus] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);
  const [status, setStatus] = useState('starting');
  const [error, setError] = useState(null);
  const [userEmail, setUserEmail] = useState(null);
  const [pushStatus, setPushStatus] = useState('Push');
  const [emailStatus, setEmailStatus] = useState('Email');

  useEffect(() => {
    const storedEmail = localStorage.getItem('userEmail');
    if (storedEmail) {
      setUserEmail(storedEmail);
    }
  }, []);

  const handleLogin = (email) => {
    localStorage.setItem('userEmail', email);
    setUserEmail(email);
  };

  const handleLogout = () => {
    localStorage.removeItem('userEmail');
    setUserEmail(null);
    resetSearch();
  };

  const handleSearch = async (query) => {
    setTopic(query);
    setIsLoading(true);
    setReport(null);
    setError(null);
    setSessionId(null);
    setStatus('starting');

    try {
      const data = await requestResearchStream(query, { push: false, email: false }, (newStatus) => {
          setStatus(newStatus);
      });

      if (data.report) {
        setReport(data.report);
        setSessionId(data.session_id);
      } else {
        throw new Error('Incomplete data received');
      }
    } catch (err) {
      setError('Something went wrong. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefine = async (feedback) => {
    if (!sessionId) return;
    setIsRefining(true);
    setError(null);
    setRefinementStatus('starting');

    try {
      const result = await refineResearch(sessionId, feedback, (progress) => {
        setRefinementStatus(progress);
      });
      
      if (result.variants) {
         setVariants(Object.entries(result.variants).map(([key, content]) => ({
           type: key === 'variant_A' ? 'analytical' : 'applied',
           content
         })));
         setComparisonData(null);
      } else if (result.updated_report && result.previous_report) {
         setComparisonData({
           previous: result.previous_report,
           updated: result.updated_report
         });
         setVariants([]);
      } else {
        throw new Error('Refinement returned unexpected format.');
      }
    } catch (err) {
      setError(err.message || 'Refinement failed.');
      console.error(err);
    } finally {
      setIsRefining(false);
      setRefinementStatus(null);
    }
  };

  const handleAcceptRefinement = async (updatedContent) => {
    try {
      await selectVariant(sessionId, updatedContent);
      setReport(updatedContent);
      setComparisonData(null);
    } catch (err) {
      console.error(err);
      setError("Failed to accept refinement.");
    }
  };

  const handleDiscardRefinement = () => {
    setComparisonData(null);
  };

  const handleSelectVariant = async (content) => {
    try {
      await selectVariant(sessionId, content);
      setReport(content);
      setVariants([]);
    } catch (err) {
      console.error(err);
      setError("Failed to select variant.");
    }
  };

  const resetSearch = () => {
    setTopic('');
    setReport(null);
    setVariants([]);
    setComparisonData(null);
    setError(null);
    setSessionId(null);
  };

  const handlePush = async () => {
    if (!sessionId) return;
    setPushStatus('Sending...');
    try {
      await deliverPush(sessionId);
      setPushStatus('Sent!');
    } catch {
      setPushStatus('Failed');
    }
    setTimeout(() => setPushStatus('Push'), 3000);
  };

  const handleEmail = async () => {
    if (!sessionId || !userEmail) return;
    setEmailStatus('Sending...');
    try {
      await deliverEmail(sessionId, userEmail);
      setEmailStatus('Sent!');
    } catch {
      setEmailStatus('Failed');
    }
    setTimeout(() => setEmailStatus('Email'), 3000);
  };

  if (!userEmail) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-paper flex flex-col items-center">
      <header className="w-full bg-white border-b border-gray-100 py-4 shadow-sm z-10 sticky top-0">
        <div className="max-w-5xl mx-auto px-4 flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <h1 className="text-2xl font-extrabold text-ink tracking-wide">AI Research Assistant</h1>
            
            {report && !isLoading && !variants.length && !comparisonData && (
              <div className="flex items-center space-x-2 border-l border-gray-100 pl-6">
                <button
                  onClick={resetSearch}
                  className="flex items-center px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-ink transition-colors"
                  title="New Search"
                >
                  <RefreshCcw size={14} className="mr-1.5" />
                  New Search
                </button>

                <button
                  onClick={handlePush}
                  disabled={pushStatus === 'Sending...'}
                  className="flex items-center px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-ink transition-colors disabled:opacity-50"
                >
                  <Bell size={14} className="mr-1.5" />
                  {pushStatus}
                </button>

                <button
                  onClick={handleEmail}
                  disabled={emailStatus === 'Sending...'}
                  className="flex items-center px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-ink transition-colors disabled:opacity-50"
                >
                  <Mail size={14} className="mr-1.5" />
                  {emailStatus}
                </button>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">{userEmail}</span>
            <button 
              onClick={handleLogout}
              className="text-xs text-gray-400 hover:text-ink transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="w-full flex-1 pt-24 max-w-5xl mx-auto">
        {/* Input Screen */}
        {!report && !isLoading && !error && (
          <div className="animate-in fade-in duration-1000">
            <div className="text-center mb-16">
            </div>
            <InputBox onSearch={handleSearch} isLoading={isLoading} />
          </div>
        )}

        {/* Loading Animation */}
        {isLoading && (
          <LoadingStatus status={status} />
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="mt-20 text-center animate-shake">
            <p className="text-ink font-medium">{error}</p>
            <button
              onClick={resetSearch}
              className="mt-4 text-sm text-gray-400 underline hover:text-ink transition-colors"
            >
              Try another topic
            </button>
          </div>
        )}

        {/* Report View */}
        {report && !isLoading && !isRefining && (
          <ReportView 
            topic={topic}
            report={report} 
            variants={variants}
            comparisonData={comparisonData}
            onSelectVariant={handleSelectVariant}
            onAcceptRefinement={handleAcceptRefinement}
            onDiscardRefinement={handleDiscardRefinement}
            onReset={resetSearch}
            onRefine={handleRefine} 
            isRefining={isRefining} 
            sessionId={sessionId}
            userEmail={userEmail}
          />
        )}

        {/* Refinement Loader */}
        {isRefining && (
          <LoadingStatus status={refinementStatus} />
        )}
      </main>
    </div>
  );
};

export default App;
