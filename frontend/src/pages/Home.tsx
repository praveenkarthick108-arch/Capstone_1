import React, { useState, useEffect, useRef, useCallback } from 'react';
import { FaultQueryResponse, QueryFilters, AgentStatus, QueryEnhancement } from '../types';
import { streamQuery, submitFeedback, followupQuery } from '../services/api';
import { saveToHistory } from './History';
import FilterPanel from '../components/FilterPanel';
import AgentPipeline from '../components/AgentPipeline';
import ResultsPanel from '../components/ResultsPanel';
import { Zap, AlertCircle, ThumbsUp, ThumbsDown, Star, Sparkles, ChevronDown, ChevronUp, Mic, MicOff, Send, MessageSquare, TrendingUp } from 'lucide-react';

const EXAMPLE_QUERIES = [
  "5G gNB sites in North region showing X2 interface failures...",
  "Multiple eNodeBs reporting S1 interface failure after maintenance...",
  "Fiber cut causing high latency between backbone nodes...",
  "MPLS LDP session flap causing traffic blackhole...",
  "PTP synchronization failure affecting 5G TDD sites...",
  "BTS towers reporting GNSS antenna failures in East region...",
];

const AGENT_NAMES = [
  "Alarm Retrieval Agent",
  "Root Cause Analysis Agent",
  "Service Impact Agent",
  "Resolution Recommendation Agent",
];

const EnhancementBanner: React.FC<{ enhancement: QueryEnhancement }> = ({ enhancement }) => {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="animate-fade-in" style={{ marginBottom: 12, padding: '10px 16px', borderRadius: 10, background: 'rgba(0,212,255,0.05)', border: '1px solid rgba(0,212,255,0.18)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }} onClick={() => setExpanded(!expanded)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Sparkles size={14} color="#00D4FF" />
          <span style={{ fontSize: 12, fontWeight: 600, color: '#00D4FF' }}>Query Enhanced</span>
          <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)' }}>— {enhancement.enhancement_notes}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {enhancement.extracted_region && (
            <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 20, background: 'rgba(0,212,255,0.08)', color: '#00D4FF', border: '1px solid rgba(0,212,255,0.2)' }}>
              📍 {enhancement.extracted_region}
            </span>
          )}
          {enhancement.extracted_technology && (
            <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 20, background: 'rgba(168,85,247,0.08)', color: '#A855F7', border: '1px solid rgba(168,85,247,0.2)' }}>
              📡 {enhancement.extracted_technology}
            </span>
          )}
          {enhancement.extracted_severity && (
            <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 20, background: 'rgba(255,140,0,0.08)', color: '#FF8C00', border: '1px solid rgba(255,140,0,0.2)' }}>
              ⚠ {enhancement.extracted_severity}
            </span>
          )}
          {expanded ? <ChevronUp size={13} color="rgba(226,232,240,0.4)" /> : <ChevronDown size={13} color="rgba(226,232,240,0.4)" />}
        </div>
      </div>
      {expanded && (
        <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div style={{ padding: '8px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: 7 }}>
            <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)', marginBottom: 4, letterSpacing: '0.5px' }}>YOUR INPUT</div>
            <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.6)', fontStyle: 'italic' }}>"{enhancement.original_query}"</div>
          </div>
          <div style={{ padding: '8px 10px', background: 'rgba(0,212,255,0.04)', borderRadius: 7, border: '1px solid rgba(0,212,255,0.1)' }}>
            <div style={{ fontSize: 10, color: '#00D4FF', marginBottom: 4, letterSpacing: '0.5px' }}>ANALYSED AS</div>
            <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.8)' }}>"{enhancement.technical_query}"</div>
          </div>
        </div>
      )}
    </div>
  );
};

interface HomeProps {
  restoredResult?: FaultQueryResponse | null;
  onResultRestored?: () => void;
}

const Home: React.FC<HomeProps> = ({ restoredResult, onResultRestored }) => {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<QueryFilters>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FaultQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [placeholderIdx, setPlaceholderIdx] = useState(0);
  const [showFilters, setShowFilters] = useState(false);
  const [feedback, setFeedback] = useState<{ rating: number; helpful: boolean | null; submitted: boolean }>({ rating: 0, helpful: null, submitted: false });

  // Streaming state
  const [streamingStatuses, setStreamingStatuses] = useState<AgentStatus[]>([]);
  const [streamingEnhancement, setStreamingEnhancement] = useState<QueryEnhancement | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Voice state
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);

  // Follow-up conversation thread
  const [followupText, setFollowupText] = useState('');
  const [followupLoading, setFollowupLoading] = useState(false);
  const [followupError, setFollowupError] = useState<string | null>(null);
  const [followupThread, setFollowupThread] = useState<{ question: string; answer: string }[]>([]);
  const followupEndRef = useRef<HTMLDivElement>(null);

  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const interval = setInterval(() => setPlaceholderIdx((i) => (i + 1) % EXAMPLE_QUERIES.length), 3500);
    return () => clearInterval(interval);
  }, []);

  // Restore a result selected from Query History
  useEffect(() => {
    if (restoredResult) {
      setResult(restoredResult);
      setStreamingStatuses(restoredResult.agent_statuses);
      setStreamingEnhancement(null);
      setError(null);
      setFollowupThread([]);
      setFeedback({ rating: 0, helpful: null, submitted: false });
      onResultRestored?.();
    }
  }, [restoredResult]);

  // ── Voice input ──────────────────────────────────────────────────
  const toggleVoice = useCallback(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      alert('Voice input is not supported in this browser. Try Chrome.');
      return;
    }
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    const rec = new SR();
    recognitionRef.current = rec;
    rec.lang = 'en-US';
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      setQuery(transcript);
      setIsListening(false);
    };
    rec.onerror = () => setIsListening(false);
    rec.onend = () => setIsListening(false);
    rec.start();
    setIsListening(true);
  }, [isListening]);

  // ── Streaming query ───────────────────────────────────────────────
  const handleQuery = async () => {
    if (!query.trim() || loading) return;

    // Abort any in-flight stream
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setLoading(true);
    setError(null);
    setResult(null);
    setFollowupText('');
    setFollowupError(null);
    setFollowupThread([]);
    setStreamingEnhancement(null);

    // All agents start as pending
    setStreamingStatuses(AGENT_NAMES.map(name => ({ name, status: 'pending' as const })));

    try {
      await streamQuery(query.trim(), filters, (event) => {
        if (event.type === 'enhanced') {
          setStreamingEnhancement(event.enhancement as QueryEnhancement);
          // Mark first agent as running
          setStreamingStatuses(prev =>
            prev.map((s, i) => i === 0 ? { ...s, status: 'running' as const } : s)
          );
        } else if (event.type === 'agent_done') {
          setStreamingStatuses(prev => {
            const idx = prev.findIndex(s => s.name === event.agent_name);
            return prev.map((s, i) => {
              if (i === idx) return { ...s, status: event.status, duration_ms: event.duration_ms };
              if (i === idx + 1) return { ...s, status: 'running' as const };
              return s;
            });
          });
        } else if (event.type === 'complete') {
          const r = { ...event.result };
          // Attach cache_hit flag from the SSE event if backend set it
          if ((event as any).cache_hit && r.cache_info) {
            r.cache_info = { ...r.cache_info, is_cache_hit: true };
          }
          setResult(r);
          setStreamingStatuses(r.agent_statuses);
          setFeedback({ rating: 0, helpful: null, submitted: false });
          saveToHistory(r);
        } else if (event.type === 'error') {
          setError(event.message);
        }
      }, ctrl.signal);
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        setError(e.message || 'Analysis failed. Please check the backend is running.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleQuery();
  };

  // ── Follow-up ─────────────────────────────────────────────────────
  const handleFollowup = async () => {
    if (!followupText.trim() || !result || followupLoading) return;
    setFollowupLoading(true);
    setFollowupError(null);
    const question = followupText.trim();
    setFollowupText('');
    try {
      const { answer } = await followupQuery({
        followup_query: question,
        prior_alarm_type: result!.alarm_retrieval.dominant_alarm_type,
        prior_region: result!.service_impact.affected_regions[0] || '',
        prior_technology: result!.alarm_retrieval.retrieved_incidents[0]?.technology_type || '',
        prior_root_cause: result!.root_cause_analysis.root_cause_chain,
        prior_query: result!.original_query,
      });
      setFollowupThread(prev => [...prev, { question, answer }]);
      // Scroll to new answer
      setTimeout(() => followupEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 100);
    } catch (e: any) {
      setFollowupError(e.response?.data?.detail || e.message || 'Follow-up failed.');
    } finally {
      setFollowupLoading(false);
    }
  };

  const handleFollowupKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleFollowup(); }
  };

  // ── Feedback ──────────────────────────────────────────────────────
  const handleFeedback = async (helpful: boolean, rating: number) => {
    if (!result || feedback.submitted) return;
    setFeedback({ rating, helpful, submitted: true });
    try {
      await submitFeedback({ query_id: result.query_id, query: result.original_query, rating, helpful });
    } catch { /* silent */ }
  };

  const showAgentPanel = loading || (streamingStatuses.length > 0 && !result);
  const agentStatusesForPanel = result ? result.agent_statuses : streamingStatuses;

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '40px 24px' }}>
      {/* Hero */}
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, marginBottom: 16, padding: '6px 16px', borderRadius: 20, background: 'rgba(0,212,255,0.08)', border: '1px solid rgba(0,212,255,0.2)' }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#00FF88', boxShadow: '0 0 6px #00FF88' }} />
          <span style={{ fontSize: 12, color: 'rgba(0,212,255,0.8)', letterSpacing: '1px' }}>AI-POWERED FAULT INTELLIGENCE</span>
        </div>
        <h1 style={{ fontSize: 'clamp(28px, 4vw, 48px)', fontWeight: 800, margin: '0 0 12px', letterSpacing: '-1px', color: '#fff', lineHeight: 1.1 }}>
          Telecom Network{' '}
          <span style={{ background: 'linear-gradient(135deg, #00D4FF, #0066CC)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Fault Intelligence
          </span>
        </h1>
        <p style={{ fontSize: 16, color: 'rgba(226,232,240,0.55)', margin: 0 }}>
          Describe any network issue in natural language — AI agents retrieve, correlate, and diagnose in real time
        </p>
      </div>

      {/* Search box */}
      <div className="glass-card" style={{ padding: 20, marginBottom: 16 }}>
        <textarea
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={EXAMPLE_QUERIES[placeholderIdx]}
          rows={3}
          style={{ width: '100%', background: 'transparent', border: 'none', outline: 'none', color: '#fff', fontSize: 15, resize: 'none', fontFamily: 'Inter, sans-serif', lineHeight: 1.6 }}
        />
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12 }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button
              onClick={() => setShowFilters(!showFilters)}
              style={{ padding: '7px 14px', borderRadius: 8, fontSize: 12, border: `1px solid ${showFilters ? 'rgba(0,212,255,0.4)' : 'rgba(255,255,255,0.1)'}`, background: showFilters ? 'rgba(0,212,255,0.08)' : 'transparent', color: showFilters ? '#00D4FF' : 'rgba(226,232,240,0.5)', cursor: 'pointer' }}
            >
              {showFilters ? 'Hide Filters' : 'Add Filters'}
            </button>
            {/* Voice button */}
            <button
              onClick={toggleVoice}
              title={isListening ? 'Stop listening' : 'Speak your query'}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 34, height: 34, borderRadius: 8, border: `1px solid ${isListening ? 'rgba(255,59,59,0.5)' : 'rgba(255,255,255,0.1)'}`, background: isListening ? 'rgba(255,59,59,0.12)' : 'transparent', color: isListening ? '#FF3B3B' : 'rgba(226,232,240,0.5)', cursor: 'pointer', transition: 'all 0.2s' }}
            >
              {isListening ? <MicOff size={15} /> : <Mic size={15} />}
            </button>
            {isListening && (
              <span style={{ fontSize: 11, color: '#FF3B3B', animation: 'pulse 1s infinite' }}>Listening...</span>
            )}
            {!isListening && <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.3)' }}>Ctrl+Enter to run</span>}
          </div>
          <button
            onClick={handleQuery}
            disabled={loading || !query.trim()}
            style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 24px', borderRadius: 10, border: 'none', cursor: loading || !query.trim() ? 'not-allowed' : 'pointer', background: loading || !query.trim() ? 'rgba(0,212,255,0.15)' : 'linear-gradient(135deg, #00D4FF, #0066CC)', color: '#fff', fontWeight: 600, fontSize: 14, transition: 'all 0.2s', boxShadow: loading || !query.trim() ? 'none' : '0 0 20px rgba(0,212,255,0.3)' }}
          >
            {loading ? (
              <><div style={{ width: 16, height: 16, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />Analyzing...</>
            ) : (
              <><Zap size={16} />Analyze Fault</>
            )}
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="glass-card animate-fade-in" style={{ padding: '16px 20px', marginBottom: 16 }}>
          <FilterPanel filters={filters} onChange={setFilters} />
        </div>
      )}

      {/* Anomaly alert — shown when incident rate is statistically above baseline */}
      {result?.anomaly_alert?.is_anomaly && (
        <div className="animate-fade-in" style={{ marginBottom: 12, padding: '12px 16px', borderRadius: 10, background: result.anomaly_alert.severity === 'HIGH' ? 'rgba(255,59,59,0.07)' : 'rgba(255,140,0,0.07)', border: `1px solid ${result.anomaly_alert.severity === 'HIGH' ? 'rgba(255,59,59,0.3)' : 'rgba(255,140,0,0.3)'}` }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <TrendingUp size={15} color={result.anomaly_alert.severity === 'HIGH' ? '#FF3B3B' : '#FF8C00'} />
            <div>
              <span style={{ fontSize: 12, fontWeight: 700, color: result.anomaly_alert.severity === 'HIGH' ? '#FF3B3B' : '#FF8C00' }}>
                Anomaly Detected — {result.anomaly_alert.combination}
              </span>
              <span style={{ fontSize: 12, color: 'rgba(226,232,240,0.65)', marginLeft: 8 }}>
                {result.anomaly_alert.multiplier}× above baseline · {result.anomaly_alert.current_rate}/mo recent vs {result.anomaly_alert.baseline_rate}/mo avg
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Cache hit banner */}
      {result?.cache_info?.is_cache_hit && (
        <div className="animate-fade-in" style={{ marginBottom: 12, padding: '10px 16px', borderRadius: 10, background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.25)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 16 }}>⚡</span>
          <div>
            <span style={{ fontSize: 12, fontWeight: 700, color: '#00FF88' }}>Cache Hit — </span>
            <span style={{ fontSize: 12, color: 'rgba(226,232,240,0.7)' }}>
              {Math.round(result.cache_info.similarity * 100)}% similar to a previous query. Zero LLM calls used.
            </span>
            <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.35)', marginLeft: 8 }}>
              Similar to: "{result.cache_info.cached_query.slice(0, 60)}{result.cache_info.cached_query.length > 60 ? '…' : ''}"
            </span>
          </div>
        </div>
      )}

      {/* Enhancement banner — appears as soon as streaming starts */}
      {(streamingEnhancement || result?.query_enhancement?.was_enhanced) && (
        <EnhancementBanner enhancement={(streamingEnhancement || result!.query_enhancement) as QueryEnhancement} />
      )}

      {/* Agent pipeline — shows live during streaming, summary after done */}
      {(showAgentPanel || result) && (
        <div className="glass-card animate-fade-in" style={{ padding: '16px 20px', marginBottom: 20 }}>
          <AgentPipeline statuses={agentStatusesForPanel} isRunning={loading} />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="glass-card animate-fade-in" style={{ padding: 16, marginBottom: 16, borderColor: 'rgba(255,59,59,0.3)', background: 'rgba(255,59,59,0.05)' }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <AlertCircle size={16} color="#FF3B3B" style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#FF3B3B', marginBottom: 4 }}>Analysis Failed</div>
              <div style={{ fontSize: 13, color: 'rgba(226,232,240,0.7)' }}>{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <>
          <ResultsPanel result={result} />

          {/* Follow-up Q&A thread */}
          {followupThread.map((entry, i) => (
            <div key={i} className="animate-fade-in" style={{ marginTop: 16 }}>
              {/* User question — right aligned */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 8 }}>
                <div style={{ maxWidth: '72%', padding: '10px 16px', borderRadius: '18px 18px 4px 18px', background: 'rgba(0,212,255,0.12)', border: '1px solid rgba(0,212,255,0.25)', fontSize: 13, color: '#fff', lineHeight: 1.5 }}>
                  {entry.question}
                </div>
              </div>
              {/* AI answer — left aligned */}
              <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'rgba(168,85,247,0.15)', border: '1px solid rgba(168,85,247,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2 }}>
                  <Sparkles size={13} color="#A855F7" />
                </div>
                <div style={{ maxWidth: '80%', padding: '10px 16px', borderRadius: '4px 18px 18px 18px', background: 'rgba(168,85,247,0.07)', border: '1px solid rgba(168,85,247,0.2)', fontSize: 13, color: 'rgba(226,232,240,0.88)', lineHeight: 1.65 }}>
                  {entry.answer}
                </div>
              </div>
            </div>
          ))}

          {/* Typing indicator while waiting for answer */}
          {followupLoading && (
            <div className="animate-fade-in" style={{ marginTop: 16 }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'rgba(168,85,247,0.15)', border: '1px solid rgba(168,85,247,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Sparkles size={13} color="#A855F7" />
                </div>
                <div style={{ padding: '12px 16px', borderRadius: '4px 18px 18px 18px', background: 'rgba(168,85,247,0.07)', border: '1px solid rgba(168,85,247,0.2)', display: 'flex', gap: 5, alignItems: 'center' }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{ width: 7, height: 7, borderRadius: '50%', background: '#A855F7', animation: `bounce 1.2s ${i * 0.2}s infinite` }} />
                  ))}
                </div>
              </div>
            </div>
          )}

          <div ref={followupEndRef} />

          {/* Follow-up input */}
          <div className="glass-card animate-fade-in" style={{ padding: '14px 18px', marginTop: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <MessageSquare size={13} color="#00D4FF" />
              <span style={{ fontSize: 12, fontWeight: 600, color: '#00D4FF' }}>Ask a follow-up</span>
              <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.35)' }}>context is carried forward automatically</span>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <input
                value={followupText}
                onChange={e => setFollowupText(e.target.value)}
                onKeyDown={handleFollowupKey}
                placeholder='e.g. "What if this was 4G instead?" or "Worst case scenario?"'
                disabled={followupLoading}
                style={{ flex: 1, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '9px 14px', color: '#fff', fontSize: 13, outline: 'none', fontFamily: 'Inter, sans-serif' }}
              />
              <button
                onClick={handleFollowup}
                disabled={!followupText.trim() || followupLoading}
                style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '9px 18px', borderRadius: 8, border: 'none', cursor: !followupText.trim() || followupLoading ? 'not-allowed' : 'pointer', background: !followupText.trim() || followupLoading ? 'rgba(0,212,255,0.1)' : 'rgba(0,212,255,0.2)', color: '#00D4FF', fontWeight: 600, fontSize: 13 }}
              >
                <Send size={14} />Ask
              </button>
            </div>
            {followupError && <div style={{ marginTop: 8, fontSize: 12, color: '#FF3B3B' }}>{followupError}</div>}
          </div>

          {/* Feedback panel */}
          <div className="glass-card animate-fade-in" style={{ padding: '16px 20px', marginTop: 16 }}>
            {feedback.submitted ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: '#00FF88' }}>
                <ThumbsUp size={16} />
                <span style={{ fontSize: 13 }}>Thank you for your feedback! It helps improve retrieval quality.</span>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                <span style={{ fontSize: 13, color: 'rgba(226,232,240,0.55)' }}>Was this analysis helpful?</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div style={{ display: 'flex', gap: 4 }}>
                    {[1, 2, 3, 4, 5].map(n => (
                      <button key={n} onClick={() => handleFeedback(n >= 3, n)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2 }}>
                        <Star size={18} fill={n <= feedback.rating ? '#FFD700' : 'none'} color={n <= feedback.rating ? '#FFD700' : 'rgba(226,232,240,0.3)'} />
                      </button>
                    ))}
                  </div>
                  <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.1)' }} />
                  <button onClick={() => handleFeedback(true, 5)} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 8, border: '1px solid rgba(0,255,136,0.2)', background: 'transparent', color: '#00FF88', cursor: 'pointer', fontSize: 12 }}>
                    <ThumbsUp size={14} /> Helpful
                  </button>
                  <button onClick={() => handleFeedback(false, 2)} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 8, border: '1px solid rgba(255,59,59,0.2)', background: 'transparent', color: '#FF3B3B', cursor: 'pointer', fontSize: 12 }}>
                    <ThumbsDown size={14} /> Not helpful
                  </button>
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* Empty state */}
      {!result && !loading && !error && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, marginTop: 20 }}>
          {['5G gNB X2 interface failures after firmware upgrade in North region',
            'Multiple eNodeBs S1 failure BGP route error on backhaul',
            'Fiber backbone latency spike between hub nodes DWDM OSNR degraded',
            'PTP grandmaster clock failure 5G NR TDD sync loss East region'].map((q, i) => (
            <button
              key={i}
              onClick={() => setQuery(q)}
              className="glass-card glass-hover"
              style={{ padding: '14px 16px', textAlign: 'left', cursor: 'pointer', border: '1px solid rgba(0,212,255,0.08)', background: 'rgba(255,255,255,0.02)', color: 'inherit', transition: 'all 0.2s' }}
            >
              <div style={{ fontSize: 10, color: 'rgba(0,212,255,0.6)', marginBottom: 6, letterSpacing: '0.5px' }}>TRY EXAMPLE</div>
              <div style={{ fontSize: 13, color: 'rgba(226,232,240,0.7)', lineHeight: 1.5 }}>{q}</div>
            </button>
          ))}
        </div>
      )}

      <style>{`
        @keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        @keyframes bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-6px)} }
      `}</style>
    </div>
  );
};

export default Home;
