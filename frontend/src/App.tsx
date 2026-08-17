import { FormEvent, useEffect, useRef, useState } from "react";
import "./App.css";

type Screen = "login" | "app";
type NavView = "dashboard" | "ask" | "history" | "knowledge" | "settings";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  confidence?: number;
  sources?: string[];
  intent?: string;
  department?: string;
};

type ConversationItem = {
  id: string;
  question: string;
  answer: string;
  confidence: number;
  sources: string[];
  timestamp: string;
  intent?: string;
  department?: string;
};

type ConfidenceFilter = "all" | "high" | "medium" | "low";

const HISTORY_STORAGE_KEY = "acsc_conversation_history";

const SUGGESTED_QUESTIONS = [
  "How do I reset my password?",
  "Why is my account locked?",
  "I cannot log in. What should I do?",
  "How can I contact support?",
];

type KnowledgeTopic = {
  id: string;
  title: string;
  icon: string;
  description: string;
  askQuestion: string;
  details: string[];
};

const KNOWLEDGE_TOPICS: KnowledgeTopic[] = [
  {
    id: "login-issues",
    title: "Login Issues",
    icon: "LI",
    description:
      "Troubleshoot login failures after a password reset or browser session problems.",
    askQuestion: "I cannot log in. What should I do?",
    details: [
      "If a user cannot log in after resetting their password:",
      "1. Ensure the new password is entered correctly.",
      "2. Clear the browser cache and cookies.",
      "3. Try using an incognito/private window.",
      "4. If the issue persists, reset the password again.",
      "5. Contact support if the account remains locked.",
    ],
  },
  {
    id: "password-reset",
    title: "Password Reset",
    icon: "PR",
    description:
      "Understand password reset email delivery timing and where to look if it is missing.",
    askQuestion: "How do I reset my password?",
    details: [
      "Password reset emails usually arrive within 5 minutes.",
      "Check the spam folder if the email is not received.",
    ],
  },
  {
    id: "account-locked",
    title: "Account Locked",
    icon: "AL",
    description:
      "Learn why accounts lock after failed attempts and how long to wait before retrying.",
    askQuestion: "Why is my account locked?",
    details: [
      "Accounts are locked after five failed login attempts.",
      "Users should wait 15 minutes before trying again or contact support.",
    ],
  },
  {
    id: "contact-support",
    title: "Contact Support",
    icon: "CS",
    description:
      "Find the support email address and official business hours for assistance.",
    askQuestion: "How can I contact support?",
    details: [
      "Email: support@example.com",
      "Business Hours:",
      "Monday to Friday",
      "9:00 AM to 6:00 PM",
    ],
  },
];

function confidenceLevel(score: number): "high" | "medium" | "low" {
  if (score >= 75) return "high";
  if (score >= 50) return "medium";
  return "low";
}

function confidenceLabel(score: number): string {
  const level = confidenceLevel(score);
  if (level === "high") return "High Confidence";
  if (level === "medium") return "Medium Confidence";
  return "Low Confidence";
}

function truncateQuestion(text: string, maxLength = 42): string {
  const trimmed = text.trim();
  if (trimmed.length <= maxLength) return trimmed;
  return `${trimmed.slice(0, maxLength - 1).trimEnd()}…`;
}

function formatConversationTime(timestamp: string): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return "Unknown time";

  const now = new Date();
  const timeLabel = date.toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });

  const startOfToday = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate()
  ).getTime();
  const startOfYesterday = startOfToday - 24 * 60 * 60 * 1000;
  const value = date.getTime();

  if (value >= startOfToday) return `Today, ${timeLabel}`;
  if (value >= startOfYesterday) return `Yesterday, ${timeLabel}`;

  const dateLabel = date.toLocaleDateString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  return `${dateLabel} • ${timeLabel}`;
}

function loadConversations(): ConversationItem[] {
  try {
    const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
    if (!raw) return [];

    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];

    return parsed
      .map((item): ConversationItem | null => {
        if (!item || typeof item !== "object") return null;
        const record = item as Record<string, unknown>;
        const id = typeof record.id === "string" ? record.id : null;
        const question =
          typeof record.question === "string" ? record.question : null;
        const answer = typeof record.answer === "string" ? record.answer : null;
        const confidence = Number(record.confidence);
        const sources = Array.isArray(record.sources)
          ? record.sources.filter(
              (source): source is string => typeof source === "string"
            )
          : [];
        const intent =
          typeof record.intent === "string" && record.intent.trim()
            ? record.intent
            : undefined;
        const department =
          typeof record.department === "string" && record.department.trim()
            ? record.department
            : undefined;
        const timestampValue = record.timestamp;
        const timestamp =
          typeof timestampValue === "string"
            ? timestampValue
            : typeof timestampValue === "number"
              ? new Date(timestampValue).toISOString()
              : null;

        if (
          !id ||
          !question ||
          !answer ||
          !timestamp ||
          Number.isNaN(confidence)
        ) {
          return null;
        }

        return {
          id,
          question,
          answer,
          confidence: Math.round(confidence),
          sources,
          timestamp,
          ...(intent ? { intent } : {}),
          ...(department ? { department } : {}),
        };
      })
      .filter((item): item is ConversationItem => item !== null);
  } catch {
    return [];
  }
}

function saveConversations(items: ConversationItem[]): void {
  try {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(items));
  } catch {
    // Ignore quota/private-mode persistence failures.
  }
}

function App() {
  const [screen, setScreen] = useState<Screen>("login");
  const [activeView, setActiveView] = useState<NavView>("ask");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [history, setHistory] = useState<ConversationItem[]>(() =>
    loadConversations()
  );
  const [activeHistoryId, setActiveHistoryId] = useState<string | null>(null);
  const [selectedConversationId, setSelectedConversationId] = useState<
    string | null
  >(null);
  const [historySearch, setHistorySearch] = useState("");
  const [historyFilter, setHistoryFilter] = useState<ConfidenceFilter>("all");
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [confirmClearHistory, setConfirmClearHistory] = useState(false);
  const [latestConfidence, setLatestConfidence] = useState<number | null>(null);
  const [latestSources, setLatestSources] = useState<string[]>([]);
  const [latestIntent, setLatestIntent] = useState<string | null>(null);
  const [latestDepartment, setLatestDepartment] = useState<string | null>(null);
  const [ticketLoading, setTicketLoading] = useState(false);
  const [ticketMessage, setTicketMessage] = useState("");
  const [latestQuestion, setLatestQuestion] = useState("");
  const [copyFeedback, setCopyFeedback] = useState("");

  const [loginLoading, setLoginLoading] = useState(false);
  const [askLoading, setAskLoading] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [askError, setAskError] = useState("");

  const [kbSearch, setKbSearch] = useState("");
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, askLoading]);

  useEffect(() => {
    saveConversations(history);
  }, [history]);

  const userInitials = email
    ? email
        .split("@")[0]
        .slice(0, 2)
        .toUpperCase()
    : "U";

  const login = async () => {
    setLoginError("");

    if (!email || !password) {
      setLoginError("Please enter your email and password.");
      return;
    }

    setLoginLoading(true);

    try {
      const body = new URLSearchParams();
      body.append("username", email);
      body.append("password", password);
      body.append("grant_type", "password");

      const response = await fetch("http://127.0.0.1:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: body.toString(),
      });

      const data = await response.json();

      if (!response.ok) {
        setLoginError(data.detail || "Invalid credentials.");
        setLoginLoading(false);
        return;
      }

      setToken(data.access_token);
      setScreen("app");
      setActiveView("ask");
    } catch {
      setLoginError(
        "Unable to connect to the server. Make sure the backend is running."
      );
    }

    setLoginLoading(false);
  };

  const askQuestion = async (selectedQuestion?: string) => {
    const finalQuestion = (selectedQuestion || question).trim();
    if (!finalQuestion || askLoading) return;

    // persist latestQuestion so ticket creation still works after question is cleared
    setLatestQuestion(finalQuestion);
    setQuestion(finalQuestion);
    setAskError("");
    setAskLoading(true);
    setCopyFeedback("");
    setActiveView("ask");
    setSidebarOpen(false);

    const userMessage: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content: finalQuestion,
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await fetch("http://127.0.0.1:8000/rag/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: finalQuestion,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setAskError(data.detail || "Unable to get an answer.");
        setAskLoading(false);
        return;
      }

      const answerText = data.answer || "No answer received.";
      const score = Math.round(Number(data.confidence_score || 0) * 100);
      const sources: string[] =
        Array.isArray(data.source_documents) && data.source_documents.length
          ? data.source_documents
          : ["Customer Support Knowledge Base"];
      const intent =
        typeof data.intent === "string" && data.intent.trim()
          ? data.intent
          : "General";
      const department =
        typeof data.department === "string" && data.department.trim()
          ? data.department
          : undefined;

      const assistantMessage: ChatMessage = {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: answerText,
        confidence: score,
        sources,
        intent,
        department,
      };

      const historyId = `h-${Date.now()}`;

      setMessages((prev) => [...prev, assistantMessage]);
      setLatestConfidence(score);
      setLatestSources(sources);
      setLatestIntent(intent);
      setLatestDepartment(department ?? null);
      setHistory((prev) => [
        {
          id: historyId,
          question: finalQuestion,
          answer: answerText,
          confidence: score,
          sources,
          intent,
          department,
          timestamp: new Date().toISOString(),
        },
        ...prev,
      ]);
      setActiveHistoryId(historyId);
      setQuestion("");
    } catch {
      setAskError(
        "Unable to connect to the server. Please check that the backend is running."
      );
    }

    setAskLoading(false);
  };

  const logout = () => {
    setToken("");
    setQuestion("");
    setMessages([]);
    setActiveHistoryId(null);
    setSelectedConversationId(null);
    setHistorySearch("");
    setHistoryFilter("all");
    setPendingDeleteId(null);
    setConfirmClearHistory(false);
    setLatestConfidence(null);
    setLatestSources([]);
    setLatestIntent(null);
    setLatestDepartment(null);
    setTicketLoading(false);
    setTicketMessage("");
    setLatestQuestion("");
    setEmail("");
    setPassword("");
    setAskError("");
    setLoginError("");
    setCopyFeedback("");
    setKbSearch("");
    setSelectedTopicId(null);
    setActiveView("ask");
    setSidebarOpen(false);
    setScreen("login");
  };

  const requestClearHistory = () => {
    if (history.length === 0) return;
    setConfirmClearHistory(true);
  };

  const confirmClearAllHistory = () => {
    setHistory([]);
    setActiveHistoryId(null);
    setSelectedConversationId(null);
    setPendingDeleteId(null);
    setConfirmClearHistory(false);
    setLatestConfidence(null);
    setLatestSources([]);
    setLatestIntent(null);
    setLatestDepartment(null);
    setTicketLoading(false);
    setTicketMessage("");
    setLatestQuestion("");
  };

  const requestDeleteConversation = (id: string) => {
    setPendingDeleteId(id);
  };

  const confirmDeleteConversation = () => {
    if (!pendingDeleteId) return;
    const deletedId = pendingDeleteId;

    setHistory((prev) => {
      const next = prev.filter((item) => item.id !== deletedId);
      if (next.length === 0) {
        setLatestConfidence(null);
        setLatestSources([]);
        setLatestIntent(null);
        setLatestDepartment(null);
      }
      return next;
    });
    if (activeHistoryId === deletedId) setActiveHistoryId(null);
    if (selectedConversationId === deletedId) setSelectedConversationId(null);
    setPendingDeleteId(null);
  };

  const copyText = async (text: string) => {
    if (!text) return;

    try {
      await navigator.clipboard.writeText(text);
      setCopyFeedback("Copied");
      setTimeout(() => setCopyFeedback(""), 2000);
    } catch {
      setCopyFeedback("Copy failed");
      setTimeout(() => setCopyFeedback(""), 2000);
    }
  };

  const copyAnswer = async () => {
    const lastAssistant = [...messages]
      .reverse()
      .find((m) => m.role === "assistant");

    if (!lastAssistant) return;
    await copyText(lastAssistant.content);
  };

  const askAnother = () => {
    setQuestion("");
    setAskError("");
    setCopyFeedback("");
    setSelectedConversationId(null);
    setActiveView("ask");
    // clear ticket UI state when asking another question
    setTicketMessage("");
    setLatestDepartment(null);
    setLatestQuestion("");
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const createTicket = async () => {
    const title = latestQuestion.trim();
    if (!title || ticketLoading) return;

    setTicketLoading(true);
    setTicketMessage("");

    try {
      const response = await fetch("http://127.0.0.1:8000/tickets/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title,
          description: title,
          attachments: [],
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        const msg = data.detail || data.message || "Unable to create ticket.";
        setTicketMessage(msg);
        setTicketLoading(false);
        return;
      }

      // Use backend-provided intent and department as source of truth
      const returnedIntent = typeof data.intent === "string" ? data.intent : null;
      const returnedDepartment = typeof data.department === "string" ? data.department : null;

      if (returnedIntent) setLatestIntent(returnedIntent);
      setLatestDepartment(returnedDepartment);

      setTicketMessage(
        `Ticket created successfully. Routed to ${returnedDepartment || "the support team"}.`
      );
    } catch (e) {
      setTicketMessage("Unable to connect to the server. Please try again.");
    }

    setTicketLoading(false);
  };

  const openConversationDetail = (item: ConversationItem) => {
    setSelectedConversationId(item.id);
    setActiveHistoryId(item.id);
    setCopyFeedback("");
    setActiveView("history");
    setSidebarOpen(false);
  };

  const loadHistoryItem = (item: ConversationItem) => {
    openConversationDetail(item);
  };

  const navigate = (view: NavView) => {
    setActiveView(view);
    setSidebarOpen(false);
    if (view !== "knowledge") {
      setSelectedTopicId(null);
    }
    if (view !== "history") {
      setSelectedConversationId(null);
      setPendingDeleteId(null);
      setConfirmClearHistory(false);
    }
  };

  const askAboutTopic = (topic: KnowledgeTopic) => {
    setSelectedTopicId(null);
    setAskError("");
    setCopyFeedback("");
    setQuestion(topic.askQuestion);
    setActiveView("ask");
    setSidebarOpen(false);
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const filteredTopics = KNOWLEDGE_TOPICS.filter((topic) => {
    const query = kbSearch.trim().toLowerCase();
    if (!query) return true;
    const haystack = [
      topic.title,
      topic.description,
      ...topic.details,
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });

  const selectedTopic =
    KNOWLEDGE_TOPICS.find((topic) => topic.id === selectedTopicId) || null;

  const onSubmitChat = (e: FormEvent) => {
    e.preventDefault();
    askQuestion();
  };

  if (screen === "login") {
    return (
      <div className="login-page">
        <div>
          <div className="login-card">
            <div className="login-logo">AC</div>
            <h1>
              Autonomous Customer
              <br />
              Support Copilot
            </h1>
            <p className="subtitle">
              Sign in to access your AI-powered support assistant
              powered by Retrieval-Augmented Generation.
            </p>

            <div className="field">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
              />
            </div>

            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") login();
                }}
                autoComplete="current-password"
              />
            </div>

            {loginError && <div className="error-banner">{loginError}</div>}

            <button
              className="btn-primary"
              onClick={login}
              disabled={loginLoading}
            >
              {loginLoading ? "Signing in..." : "Sign In"}
            </button>

            <p className="login-meta">Secure JWT Authentication</p>
          </div>
          <p className="login-footer">
            Autonomous Customer Support Copilot · AI + RAG
          </p>
        </div>
      </div>
    );
  }

  const level =
    latestConfidence === null ? null : confidenceLevel(latestConfidence);

  const questionsAsked = history.length;
  const averageConfidence =
    questionsAsked === 0
      ? null
      : Math.round(
          history.reduce((sum, item) => sum + item.confidence, 0) /
            questionsAsked
        );

  const filteredConversations = history.filter((item) => {
    const query = historySearch.trim().toLowerCase();
    const matchesSearch =
      !query ||
      item.question.toLowerCase().includes(query) ||
      item.answer.toLowerCase().includes(query) ||
      item.sources.some((source) => source.toLowerCase().includes(query));

    if (!matchesSearch) return false;

    if (historyFilter === "all") return true;
    return confidenceLevel(item.confidence) === historyFilter;
  });

  const selectedConversation =
    history.find((item) => item.id === selectedConversationId) || null;

  const pendingDeleteItem =
    history.find((item) => item.id === pendingDeleteId) || null;

  return (
    <div className="app-shell">
      {sidebarOpen && (
        <div className="overlay" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-brand">
          <div className="sidebar-brand-mark">AC</div>
          <div className="sidebar-brand-text">
            Autonomous Customer
            <br />
            Support Copilot
          </div>
        </div>

        <nav className="nav-list">
          <button
            className={`nav-item ${activeView === "dashboard" ? "active" : ""}`}
            onClick={() => navigate("dashboard")}
          >
            <span className="nav-icon">▣</span>
            Dashboard
          </button>
          <button
            className={`nav-item ${activeView === "ask" ? "active" : ""}`}
            onClick={() => navigate("ask")}
          >
            <span className="nav-icon">✦</span>
            Ask AI
          </button>
          <button
            className={`nav-item ${activeView === "history" ? "active" : ""}`}
            onClick={() => navigate("history")}
          >
            <span className="nav-icon">◷</span>
            Conversation History
          </button>
          <button
            className={`nav-item ${activeView === "knowledge" ? "active" : ""}`}
            onClick={() => navigate("knowledge")}
          >
            <span className="nav-icon">▤</span>
            Knowledge Base
          </button>
          <button
            className={`nav-item ${activeView === "settings" ? "active" : ""}`}
            onClick={() => navigate("settings")}
          >
            <span className="nav-icon">⚙</span>
            Settings
          </button>
        </nav>

        <div className="sidebar-history">
          <div className="sidebar-history-header">
            <span>Conversation History</span>
            {history.length > 0 && (
              <button
                type="button"
                className="clear-history-btn"
                onClick={requestClearHistory}
              >
                Clear History
              </button>
            )}
          </div>

          {history.length === 0 ? (
            <p className="sidebar-history-empty">No conversations yet.</p>
          ) : (
            <div className="sidebar-history-list">
              {history.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`sidebar-history-item${
                    activeHistoryId === item.id ? " active" : ""
                  }`}
                  onClick={() => loadHistoryItem(item)}
                  title={item.question}
                >
                  {truncateQuestion(item.question)}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="sidebar-footer">
          <button className="nav-item nav-logout" onClick={logout}>
            <span className="nav-icon">↩</span>
            Logout
          </button>
        </div>
      </aside>

      <div className="shell-main">
        <header className="top-header">
          <div className="header-left">
            <button
              className="menu-toggle"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open menu"
            >
              ☰
            </button>
            <h1 className="header-title">AI Support Assistant</h1>
            <div className="status-pill">
              <span className="status-dot" />
              Online
            </div>
          </div>

          <div className="user-chip">
            <div className="user-avatar">{userInitials}</div>
            <div className="user-meta">
              <strong>{email.split("@")[0]}</strong>
              <span>{email}</span>
            </div>
          </div>
        </header>

        <main className="content-area">
          {activeView === "dashboard" && (
            <div className="dashboard-page">
              <div className="dashboard-header">
                <div>
                  <h2>AI Support Dashboard</h2>
                  <p className="lead">
                    Monitor your customer support AI assistant
                  </p>
                </div>
              </div>

              <div className="dash-stat-grid">
                <div className="dash-stat-card">
                  <span className="dash-stat-label">Questions Asked</span>
                  <strong className="dash-stat-value">{questionsAsked}</strong>
                  <span className="dash-stat-hint">
                    Successfully answered this session
                  </span>
                </div>

                <div className="dash-stat-card">
                  <span className="dash-stat-label">Average Confidence</span>
                  <strong className="dash-stat-value">
                    {averageConfidence === null
                      ? "—"
                      : `${averageConfidence}%`}
                  </strong>
                  <span className="dash-stat-hint">
                    From actual AI responses
                  </span>
                </div>

                <div className="dash-stat-card">
                  <span className="dash-stat-label">Knowledge Documents</span>
                  <strong className="dash-stat-value">1</strong>
                  <span className="dash-stat-hint">Indexed Document</span>
                </div>

                <div className="dash-stat-card accent">
                  <span className="dash-stat-label">RAG Status</span>
                  <strong className="dash-stat-value online-row">
                    <span className="online-dot" />
                    Online
                  </strong>
                  <span className="dash-stat-hint">
                    Connected to knowledge base
                  </span>
                </div>
              </div>

              <div className="dashboard-grid">
                <section className="dash-panel">
                  <div className="dash-panel-header">
                    <h3>Recent Questions</h3>
                    <span className="dash-panel-meta">
                      {questionsAsked} this session
                    </span>
                  </div>

                  {history.length === 0 ? (
                    <div className="dash-empty">
                      <p>No questions asked yet.</p>
                      <p>Start a conversation with your AI Copilot.</p>
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => navigate("ask")}
                      >
                        Ask AI
                      </button>
                    </div>
                  ) : (
                    <div className="recent-list">
                      {history.map((item) => {
                        const itemLevel = confidenceLevel(item.confidence);
                        const sourceLabel =
                          item.sources[0] || "Customer Support Knowledge Base";

                        return (
                          <button
                            key={item.id}
                            type="button"
                            className="recent-item"
                            onClick={() => loadHistoryItem(item)}
                          >
                            <div className="recent-top">
                              <span
                                className={`recent-status ${itemLevel}`}
                                title={confidenceLabel(item.confidence)}
                              />
                              <p className="recent-question">{item.question}</p>
                            </div>
                            <div className="recent-meta">
                              <span>{item.confidence}% confidence</span>
                              <span className="recent-source">
                                {truncateQuestion(sourceLabel, 36)}
                              </span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </section>

                <div className="dashboard-side">
                  <section className="dash-panel">
                    <div className="dash-panel-header">
                      <h3>Confidence Overview</h3>
                    </div>

                    {history.length === 0 ? (
                      <div className="dash-empty compact">
                        <p>
                          Confidence bars will appear after your first AI
                          response.
                        </p>
                      </div>
                    ) : (
                      <div className="confidence-overview">
                        {history.map((item) => {
                          const itemLevel = confidenceLevel(item.confidence);
                          return (
                            <div
                              className="confidence-row"
                              key={`conf-${item.id}`}
                            >
                              <div className="confidence-row-top">
                                <span title={item.question}>
                                  {truncateQuestion(item.question, 28)}
                                </span>
                                <strong>{item.confidence}%</strong>
                              </div>
                              <div className="progress-track">
                                <div
                                  className={`progress-fill ${itemLevel}`}
                                  style={{ width: `${item.confidence}%` }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </section>

                  <section className="dash-panel rag-panel">
                    <div className="dash-panel-header">
                      <h3>RAG System</h3>
                      <span className="rag-online">
                        <span className="online-dot" />
                        Online
                      </span>
                    </div>
                    <p className="rag-description">
                      Your AI Copilot is connected to the support knowledge
                      base.
                    </p>
                    <ul className="rag-status-list">
                      <li>
                        <span>Vector Database</span>
                        <strong className="status-ok">Connected</strong>
                      </li>
                      <li>
                        <span>Knowledge Base</span>
                        <strong className="status-ok">Available</strong>
                      </li>
                      <li>
                        <span>AI Assistant</span>
                        <strong className="status-ok">Ready</strong>
                      </li>
                    </ul>
                  </section>
                </div>
              </div>

              <section className="dash-panel quick-panel">
                <div className="dash-panel-header">
                  <h3>Quick Actions</h3>
                </div>
                <div className="dash-quick-grid">
                  <button
                    type="button"
                    className="dash-quick-card"
                    onClick={() => navigate("ask")}
                  >
                    <span className="dash-quick-icon">AI</span>
                    <strong>Ask AI</strong>
                    <span>Open the support chat assistant</span>
                  </button>
                  <button
                    type="button"
                    className="dash-quick-card"
                    onClick={() => navigate("knowledge")}
                  >
                    <span className="dash-quick-icon">KB</span>
                    <strong>Knowledge Base</strong>
                    <span>Browse indexed support topics</span>
                  </button>
                  <button
                    type="button"
                    className="dash-quick-card"
                    onClick={() => navigate("history")}
                  >
                    <span className="dash-quick-icon">CH</span>
                    <strong>Conversation History</strong>
                    <span>Review earlier session questions</span>
                  </button>
                </div>
              </section>
            </div>
          )}

          {activeView === "ask" && (
            <div className="chat-layout">
              <section className="chat-panel">
                <div className="chat-messages">
                  {messages.length === 0 && !askLoading && (
                    <>
                      <div className="welcome-block">
                        <div className="welcome-avatar">AI</div>
                        <h2>Hello! I&apos;m your AI Support Copilot.</h2>
                        <p>
                          Ask me anything about your support documents.
                        </p>
                      </div>

                      <div className="suggestions">
                        {SUGGESTED_QUESTIONS.map((q) => (
                          <button
                            key={q}
                            className="suggestion-chip"
                            disabled={askLoading}
                            onClick={() => askQuestion(q)}
                          >
                            {q}
                          </button>
                        ))}
                      </div>
                    </>
                  )}

                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`message-row ${msg.role}`}
                    >
                      <div className={`bubble ${msg.role}`}>
                        <div className="bubble-meta">
                          {msg.role === "user" ? "You" : "AI Copilot"}
                        </div>
                        {msg.content}
                      </div>
                    </div>
                  ))}

                  {askLoading && (
                    <div className="message-row assistant">
                      <div className="typing" aria-label="AI is thinking">
                        <span />
                        <span />
                        <span />
                      </div>
                    </div>
                  )}

                  {askError && <div className="error-banner">{askError}</div>}

                  <div ref={messagesEndRef} />
                </div>

                <div className="chat-input-bar">
                  <form className="chat-input-row" onSubmit={onSubmitChat}>
                    <input
                      ref={inputRef}
                      type="text"
                      placeholder="Ask a support question..."
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      disabled={askLoading}
                    />
                    <button
                      type="submit"
                      className="send-btn"
                      disabled={askLoading || !question.trim()}
                      aria-label="Send"
                    >
                      →
                    </button>
                  </form>

                  <div className="chat-actions">
                    <button
                      className="action-btn"
                      onClick={copyAnswer}
                      disabled={
                        askLoading ||
                        !messages.some((m) => m.role === "assistant")
                      }
                    >
                      {copyFeedback || "Copy Answer"}
                    </button>
                    <button
                      className="action-btn"
                      onClick={askAnother}
                      disabled={askLoading}
                    >
                      Ask another question
                    </button>
                    <button
                      className="action-btn"
                      onClick={createTicket}
                      disabled={ticketLoading || !latestQuestion.trim()}
                    >
                      {ticketLoading ? "Creating Ticket..." : "Create Support Ticket"}
                    </button>
                  </div>
                  {ticketMessage && (
                    <div style={{ marginTop: 10 }}>
                      {ticketMessage.includes("Ticket created") ? (
                        <div className="ticket-message ticket-success">
                          {ticketMessage}
                        </div>
                      ) : (
                        <div className="error-banner">{ticketMessage}</div>
                      )}
                    </div>
                  )}
                </div>
              </section>

              <aside className="side-cards">
                {latestConfidence !== null && level ? (
                  <div className="info-card">
                    <h3>Confidence</h3>
                    <div className={`confidence-value ${level}`}>
                      {latestConfidence}%
                    </div>
                    <div className={`confidence-label ${level}`}>
                      {confidenceLabel(latestConfidence)}
                    </div>
                    <div className="progress-track">
                      <div
                        className={`progress-fill ${level}`}
                        style={{ width: `${latestConfidence}%` }}
                      />
                    </div>
                    <p className="hint">
                      Confidence based on retrieved knowledge and
                      question relevance.
                    </p>
                  </div>
                ) : (
                  <div className="placeholder-card">
                    <strong>Confidence</strong>
                    <span>
                      Ask a question to see confidence scoring for the
                      AI response.
                    </span>
                  </div>
                )}

                {latestIntent ? (
                  <div className="info-card">
                    <h3>Intent</h3>
                    <div className="intent-value">{latestIntent}</div>
                    {latestDepartment && (
                      <>
                        <div className="hint" style={{ marginTop: 10, fontWeight: 700 }}>
                          Department
                        </div>
                        <div style={{ marginTop: 8 }}>{latestDepartment}</div>
                      </>
                    )}
                    <p className="hint">
                      Detected from the latest RAG response.
                    </p>
                  </div>
                ) : (
                  <div className="placeholder-card">
                    <strong>Intent</strong>
                    <span>
                      The detected intent will appear here after each
                      answer.
                    </span>
                  </div>
                )}

                {latestSources.length > 0 ? (
                  <div className="info-card">
                    <h3>Sources</h3>
                    <div className="source-list">
                      {latestSources.map((source, index) => (
                        <div className="source-item" key={`${source}-${index}`}>
                          <div className="source-icon">
                            {index + 1}
                          </div>
                          <span>{source}</span>
                        </div>
                      ))}
                    </div>
                    <p className="hint" style={{ marginTop: 12 }}>
                      Retrieved from your support knowledge base.
                    </p>
                  </div>
                ) : (
                  <div className="placeholder-card">
                    <strong>Sources</strong>
                    <span>
                      Source documents will appear here after each
                      answer.
                    </span>
                  </div>
                )}
              </aside>
            </div>
          )}

          {activeView === "history" && (
            <div className="history-page">
              {selectedConversation ? (
                <div className="history-detail">
                  <div className="history-detail-top">
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => setSelectedConversationId(null)}
                    >
                      ← Back to History
                    </button>
                    <span
                      className={`confidence-badge ${confidenceLevel(
                        selectedConversation.confidence
                      )}`}
                    >
                      {confidenceLabel(selectedConversation.confidence)}
                    </span>
                  </div>

                  <h2>Conversation Details</h2>
                  <p className="lead">
                    {formatConversationTime(selectedConversation.timestamp)}
                  </p>

                  <section className="history-detail-card">
                    <h3>User Question</h3>
                    <p>{selectedConversation.question}</p>
                  </section>

                  <section className="history-detail-card answer">
                    <h3>AI Copilot Answer</h3>
                    <p>{selectedConversation.answer}</p>
                  </section>

                  <div className="history-detail-grid">
                    <section className="history-detail-card">
                      <h3>Confidence</h3>
                      <div
                        className={`confidence-value ${confidenceLevel(
                          selectedConversation.confidence
                        )}`}
                      >
                        {selectedConversation.confidence}%
                      </div>
                      <div className="progress-track">
                        <div
                          className={`progress-fill ${confidenceLevel(
                            selectedConversation.confidence
                          )}`}
                          style={{
                            width: `${selectedConversation.confidence}%`,
                          }}
                        />
                      </div>
                      <p className="hint">
                        Confidence based on retrieved knowledge and question
                        relevance.
                      </p>
                    </section>

                    <section className="history-detail-card">
                      <h3>Sources</h3>
                      <div className="source-list">
                        {selectedConversation.sources.map((source, index) => (
                          <div
                            className="source-item"
                            key={`${selectedConversation.id}-src-${index}`}
                          >
                            <div className="source-icon">{index + 1}</div>
                            <span>{source}</span>
                          </div>
                        ))}
                      </div>
                    </section>
                  </div>

                  <div className="history-detail-actions">
                    <button
                      type="button"
                      className="action-btn"
                      onClick={() => copyText(selectedConversation.answer)}
                    >
                      {copyFeedback || "Copy Answer"}
                    </button>
                    <button
                      type="button"
                      className="action-btn"
                      onClick={askAnother}
                    >
                      Ask another question
                    </button>
                    <button
                      type="button"
                      className="action-btn danger"
                      onClick={() =>
                        requestDeleteConversation(selectedConversation.id)
                      }
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="history-page-header">
                    <div>
                      <h2>Conversation History</h2>
                      <p className="lead">
                        Review and manage your AI support conversations
                      </p>
                    </div>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={requestClearHistory}
                      disabled={history.length === 0}
                    >
                      Clear History
                    </button>
                  </div>

                  {history.length === 0 ? (
                    <div className="history-empty">
                      <h3>No conversations yet</h3>
                      <p>
                        Ask your AI Support Copilot a question and your
                        conversations will appear here.
                      </p>
                      <button
                        type="button"
                        className="kb-ask-btn"
                        onClick={() => navigate("ask")}
                      >
                        Ask AI
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="history-toolbar">
                        <input
                          type="search"
                          className="history-search"
                          placeholder="Search conversations..."
                          value={historySearch}
                          onChange={(e) => setHistorySearch(e.target.value)}
                        />
                        <div className="history-filters">
                          {(
                            [
                              ["all", "All"],
                              ["high", "High Confidence"],
                              ["medium", "Medium Confidence"],
                              ["low", "Low Confidence"],
                            ] as const
                          ).map(([value, label]) => (
                            <button
                              key={value}
                              type="button"
                              className={`history-filter-btn${
                                historyFilter === value ? " active" : ""
                              }`}
                              onClick={() => setHistoryFilter(value)}
                            >
                              {label}
                            </button>
                          ))}
                        </div>
                      </div>

                      {filteredConversations.length === 0 ? (
                        <div className="history-empty compact">
                          <h3>No conversations found.</h3>
                          <p>
                            Try a different search term or confidence filter.
                          </p>
                        </div>
                      ) : (
                        <div className="conversation-list">
                          {filteredConversations.map((item) => {
                            const itemLevel = confidenceLevel(item.confidence);
                            const sourceLabel =
                              item.sources[0] ||
                              "Customer Support Knowledge Base";

                            return (
                              <article
                                className={`conversation-card${
                                  activeHistoryId === item.id ? " active" : ""
                                }`}
                                key={item.id}
                              >
                                <div className="conversation-card-main">
                                  <h3>{item.question}</h3>
                                  <p className="conversation-card-meta">
                                    AI answered • {item.confidence}% confidence
                                  </p>
                                  <p className="conversation-card-source">
                                    {truncateQuestion(sourceLabel, 40)} •{" "}
                                    {formatConversationTime(item.timestamp)}
                                  </p>
                                  <span
                                    className={`confidence-badge ${itemLevel}`}
                                  >
                                    {confidenceLabel(item.confidence)}
                                  </span>
                                </div>
                                <div className="conversation-card-actions">
                                  <button
                                    type="button"
                                    className="conversation-view-btn"
                                    onClick={() => openConversationDetail(item)}
                                  >
                                    View →
                                  </button>
                                  <button
                                    type="button"
                                    className="conversation-delete-btn"
                                    onClick={() =>
                                      requestDeleteConversation(item.id)
                                    }
                                  >
                                    Delete
                                  </button>
                                </div>
                              </article>
                            );
                          })}
                        </div>
                      )}
                    </>
                  )}
                </>
              )}
            </div>
          )}

          {activeView === "knowledge" && (
            <div className="kb-page">
              <div className="kb-header">
                <div>
                  <h2>Knowledge Base</h2>
                  <p className="lead">
                    Support information used by your AI Copilot
                  </p>
                </div>
                <div className="kb-doc-chip">
                  <span className="kb-doc-mark">DOC</span>
                  <div>
                    <strong>support_faq.txt</strong>
                    <span>Indexed support document</span>
                  </div>
                </div>
              </div>

              <div className="kb-summary">
                <div className="kb-summary-card">
                  <span className="kb-summary-label">Topics</span>
                  <strong>4 Topics</strong>
                </div>
                <div className="kb-summary-card">
                  <span className="kb-summary-label">Documents</span>
                  <strong>1 Document</strong>
                </div>
                <div className="kb-summary-card accent">
                  <span className="kb-summary-label">Status</span>
                  <strong>RAG Enabled</strong>
                </div>
              </div>

              <div className="kb-toolbar">
                <input
                  type="search"
                  className="kb-search"
                  placeholder="Search knowledge base..."
                  value={kbSearch}
                  onChange={(e) => setKbSearch(e.target.value)}
                />
              </div>

              {filteredTopics.length === 0 ? (
                <div className="kb-empty">
                  No topics match your search.
                </div>
              ) : (
                <div className="kb-grid">
                  {filteredTopics.map((topic) => (
                    <article className="kb-card" key={topic.id}>
                      <div className="kb-card-icon" aria-hidden="true">
                        {topic.icon}
                      </div>
                      <h3>{topic.title}</h3>
                      <p>{topic.description}</p>
                      <button
                        type="button"
                        className="kb-view-btn"
                        onClick={() => setSelectedTopicId(topic.id)}
                      >
                        View Details
                      </button>
                    </article>
                  ))}
                </div>
              )}

              {selectedTopic && (
                <div
                  className="kb-modal-backdrop"
                  onClick={() => setSelectedTopicId(null)}
                >
                  <div
                    className="kb-modal"
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="kb-modal-title"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="kb-modal-header">
                      <div className="kb-modal-title-row">
                        <span className="kb-card-icon">{selectedTopic.icon}</span>
                        <div>
                          <p className="kb-modal-eyebrow">Topic details</p>
                          <h3 id="kb-modal-title">{selectedTopic.title}</h3>
                        </div>
                      </div>
                      <button
                        type="button"
                        className="kb-modal-close"
                        onClick={() => setSelectedTopicId(null)}
                        aria-label="Close"
                      >
                        ×
                      </button>
                    </div>

                    <div className="kb-modal-body">
                      {selectedTopic.details.map((line) => (
                        <p key={line}>{line}</p>
                      ))}
                    </div>

                    <div className="kb-modal-actions">
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => setSelectedTopicId(null)}
                      >
                        Close
                      </button>
                      <button
                        type="button"
                        className="kb-ask-btn"
                        onClick={() => askAboutTopic(selectedTopic)}
                      >
                        Ask AI about this
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeView === "settings" && (
            <div className="panel">
              <h2>Settings</h2>
              <p className="lead">
                Account and session preferences for this workspace.
              </p>

              <div className="settings-row">
                <div>
                  <strong>Signed-in account</strong>
                  <span>{email}</span>
                </div>
                <span className="badge">Active</span>
              </div>

              <div className="settings-row">
                <div>
                  <strong>Authentication</strong>
                  <span>JWT Bearer token</span>
                </div>
                <span className="badge">Secure</span>
              </div>

              <div className="settings-row">
                <div>
                  <strong>API endpoint</strong>
                  <span>http://127.0.0.1:8000/rag/query</span>
                </div>
                <span className="badge">Connected</span>
              </div>

              <div style={{ marginTop: 20 }}>
                <button className="btn-secondary" onClick={logout}>
                  Sign out
                </button>
              </div>
            </div>
          )}

          {pendingDeleteItem && (
            <div
              className="confirm-backdrop"
              onClick={() => setPendingDeleteId(null)}
            >
              <div
                className="confirm-modal"
                role="dialog"
                aria-modal="true"
                onClick={(e) => e.stopPropagation()}
              >
                <h3>Delete this conversation?</h3>
                <p>
                  This will permanently remove the selected conversation from
                  history.
                </p>
                <div className="confirm-actions">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setPendingDeleteId(null)}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="confirm-danger-btn"
                    onClick={confirmDeleteConversation}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          )}

          {confirmClearHistory && (
            <div
              className="confirm-backdrop"
              onClick={() => setConfirmClearHistory(false)}
            >
              <div
                className="confirm-modal"
                role="dialog"
                aria-modal="true"
                onClick={(e) => e.stopPropagation()}
              >
                <h3>
                  Are you sure you want to clear all conversation history?
                </h3>
                <p>
                  This removes every saved conversation from this browser. Your
                  login and knowledge base are not affected.
                </p>
                <div className="confirm-actions">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setConfirmClearHistory(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="confirm-danger-btn"
                    onClick={confirmClearAllHistory}
                  >
                    Clear History
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
