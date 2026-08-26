import {
  Activity,
  Bot,
  ChartNoAxesCombined,
  CircleAlert,
  CircleCheck,
  CircleMinus,
  LibraryBig,
  LoaderCircle,
  MessageCircle,
  Minus,
  Sparkles,
  Trophy,
  X,
} from "lucide-react";
import {
  type KeyboardEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import apiClient from "../../api/client";
import "../../styles/components/chatbot/ChatbotWidget.css";

type ChatbotWidgetProps = {
  displayName?: string | null;
};

type ChatbotTableResponse = {
  type: "table";
  message: string;
  columns: string[];
  rows: Record<string, unknown>[];
  total_rows: number;
};

type ChatbotTextResponse = {
  type: "text";
  message: string;
  columns: string[];
  rows: Record<string, unknown>[];
  total_rows: number;
};

type ChatbotReportInsight = {
  status: "positive" | "warning" | "negative" | "neutral";
  icon: string;
  label: string;
  value: string;
  detail?: string | null;
};

type ChatbotReportResponse = {
  type: "report";
  title: string;
  message: string;
  insights: ChatbotReportInsight[];
};

type ChatbotResponse =
  | ChatbotTextResponse
  | ChatbotTableResponse
  | ChatbotReportResponse;

type ChatMessage =
  | {
    id: string;
    role: "user";
    text: string;
  }
  | {
    id: string;
    role: "assistant";
    response: ChatbotResponse;
  }
  | {
    id: string;
    role: "error";
    text: string;
  };

const suggestions = [
  "What should I study next?",
  "How am I improving?",
  "My monthly report",
];

const CHATBOT_MESSAGES_STORAGE_KEY =
  "quizapp_chatbot_messages";

function loadStoredMessages(): ChatMessage[] {
  try {
    const storedMessages = window.sessionStorage.getItem(
      CHATBOT_MESSAGES_STORAGE_KEY,
    );

    if (!storedMessages) {
      return [];
    }

    const parsedMessages = JSON.parse(storedMessages);

    return Array.isArray(parsedMessages)
      ? (parsedMessages as ChatMessage[])
      : [];
  } catch {
    return [];
  }
}

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function formatColumnLabel(column: string) {
  return column
    .replace(/_id$/i, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatCellValue(column: string, value: unknown) {
  if (value === null || value === undefined) {
    return "—";
  }

  if (
    typeof value === "number" &&
    (column === "average_score" ||
      column === "score_percentage" ||
      column === "miss_rate")
  ) {
    return `${value}%`;
  }

  if (
    (column === "submitted_at" || column === "created_at") &&
    typeof value === "string"
  ) {
    const date = new Date(value);

    if (!Number.isNaN(date.getTime())) {
      if (column === "created_at") {
        return date.toLocaleDateString([], {
          dateStyle: "medium",
        });
      }

      return date.toLocaleString([], {
        dateStyle: "medium",
        timeStyle: "short",
      });
    }
  }

  return String(value);
}

function getVisibleColumns(columns: string[]) {
  return columns.filter(
    (column) =>
      column !== "quiz_id" &&
      column !== "question_id" &&
      column !== "attempt_id",
  );
}

function getReportIcon(icon: string) {
  const normalizedIcon = icon.trim().toLowerCase();

  switch (normalizedIcon) {
    case "chart-no-axes-combined":
      return ChartNoAxesCombined;
    case "activity":
      return Activity;
    case "library-big":
      return LibraryBig;
    case "trophy":
      return Trophy;
    default:
      return Sparkles;
  }
}

function getReportStatusIcon(
  status: ChatbotReportInsight["status"],
) {
  switch (status) {
    case "positive":
      return CircleCheck;
    case "warning":
      return CircleAlert;
    case "negative":
      return CircleAlert;
    default:
      return CircleMinus;
  }
}

function ChatbotWidget({ displayName }: ChatbotWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] =
    useState<ChatMessage[]>(loadStoredMessages);
  const [isSending, setIsSending] = useState(false);

  const bodyRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (!isClosing) {
      return;
    }

    const timeout = window.setTimeout(() => {
      setIsOpen(false);
      setIsClosing(false);
    }, 180);

    return () => window.clearTimeout(timeout);
  }, [isClosing]);

  useEffect(() => {
    try {
      window.sessionStorage.setItem(
        CHATBOT_MESSAGES_STORAGE_KEY,
        JSON.stringify(messages),
      );
    } catch {
      // Chat still works if sessionStorage is unavailable.
    }
  }, [messages]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const body = bodyRef.current;

    if (body) {
      body.scrollTo({
        top: body.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, isSending, isOpen]);

  const closeChatbot = () => {
    if (!isClosing) {
      setIsClosing(true);
    }
  };

  const firstName = displayName?.trim().split(/\s+/)[0] || "there";

  const sendMessage = async (message?: string) => {
    const normalizedMessage = (message ?? input).trim();

    if (!normalizedMessage || isSending) {
      return;
    }

    setMessages((current) => [
      ...current,
      {
        id: createMessageId(),
        role: "user",
        text: normalizedMessage,
      },
    ]);

    setInput("");
    setIsSending(true);

    try {
      const response = await apiClient.post<ChatbotResponse>(
        "/chatbot",
        {
          message: normalizedMessage,
        },
      );

      setMessages((current) => [
        ...current,
        {
          id: createMessageId(),
          role: "assistant",
          response: response.data,
        },
      ]);
    } catch {
      setMessages((current) => [
        ...current,
        {
          id: createMessageId(),
          role: "error",
          text:
            "I couldn't answer that right now. Please try again in a moment.",
        },
      ]);
    } finally {
      setIsSending(false);

      window.setTimeout(() => {
        textareaRef.current?.focus();
      }, 0);
    }
  };

  const handleKeyDown = (
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      void sendMessage();
    }
  };

  const renderAssistantResponse = (
    response: ChatbotResponse,
  ) => {
    if (response.type === "text") {
      return (
        <div className="chatbot-message chatbot-message--assistant">
          <p>{response.message}</p>
        </div>
      );
    }

    if (response.type === "report") {
      return (
        <div className="chatbot-message chatbot-message--assistant chatbot-report">
          <strong className="chatbot-report__title">
            {response.title}
          </strong>

          <p>{response.message}</p>

          <div className="chatbot-report__insights">
            {response.insights.map((insight, index) => {
              const InsightIcon = getReportIcon(insight.icon);
              const StatusIcon = getReportStatusIcon(
                insight.status,
              );

              return (
                <div
                  className={`chatbot-report__insight chatbot-report__insight--${insight.status}`}
                  key={`${insight.label}-${index}`}
                >
                  <div
                    className="chatbot-report__icon"
                    aria-hidden="true"
                  >
                    <InsightIcon
                      size={19}
                      strokeWidth={2}
                    />
                  </div>

                  <div className="chatbot-report__content">
                    <div className="chatbot-report__heading">
                      <span className="chatbot-report__label">
                        {insight.label}
                      </span>

                      <StatusIcon
                        className="chatbot-report__status-icon"
                        size={14}
                        strokeWidth={2}
                        aria-hidden="true"
                      />
                    </div>

                    <strong className="chatbot-report__value">
                      {insight.value}
                    </strong>

                    {insight.detail && (
                      <small>{insight.detail}</small>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    const visibleColumns = getVisibleColumns(response.columns);

    return (
      <div className="chatbot-message chatbot-message--assistant chatbot-table-message">
        <p>{response.message}</p>

        {response.rows.length > 0 && (
          <div className="chatbot-table-scroll">
            <table className="chatbot-table">
              <thead>
                <tr>
                  {visibleColumns.map((column) => (
                    <th key={column}>
                      {formatColumnLabel(column)}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {response.rows.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    {visibleColumns.map((column) => (
                      <td key={column}>
                        {formatCellValue(column, row[column])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="chatbot-widget">
      {isOpen && (
        <section
          className={`chatbot-panel${isClosing ? " chatbot-panel--closing" : ""
            }`}
          role="dialog"
          aria-label="QuizApp AI assistant"
        >
          <header className="chatbot-header">
            <div className="chatbot-header__identity">
              <div
                className="chatbot-header__avatar"
                aria-hidden="true"
              >
                <Bot size={25} strokeWidth={2.2} />
                <span className="chatbot-header__status-dot" />
              </div>

              <div className="chatbot-header__text">
                <div className="chatbot-header__title">
                  <strong>QuizApp AI</strong>
                  <Sparkles
                    size={16}
                    strokeWidth={2}
                    aria-hidden="true"
                  />
                </div>

                <span className="chatbot-header__status">
                  <i aria-hidden="true" />
                  Online
                  <b aria-hidden="true">•</b>
                  Always here to help!
                </span>
              </div>
            </div>

            <div className="chatbot-header__actions">
              <button
                type="button"
                aria-label="Minimize chatbot"
                onClick={closeChatbot}
              >
                <Minus size={22} strokeWidth={2} />
              </button>

              <button
                type="button"
                aria-label="Close chatbot"
                onClick={closeChatbot}
              >
                <X size={22} strokeWidth={2} />
              </button>
            </div>
          </header>

          <div className="chatbot-body" ref={bodyRef}>
            <div className="chatbot-message-row chatbot-message-row--assistant">
              <div
                className="chatbot-message-avatar"
                aria-hidden="true"
              >
                <Bot size={19} strokeWidth={2.2} />
              </div>

              <div className="chatbot-message-group">
                <div className="chatbot-message chatbot-message--assistant">
                  <p>
                    Hi {firstName}!{" "}
                    <span aria-hidden="true">👋</span>
                  </p>
                  <p>I'm your QuizApp assistant.</p>
                  <p>How can I help you today?</p>
                </div>
              </div>
            </div>

            {messages.map((message) => {
              if (message.role === "user") {
                return (
                  <div
                    className="chatbot-message-row chatbot-message-row--user"
                    key={message.id}
                  >
                    <div className="chatbot-message-group">
                      <div className="chatbot-message chatbot-message--user">
                        <p>{message.text}</p>
                      </div>
                    </div>
                  </div>
                );
              }

              if (message.role === "error") {
                return (
                  <div
                    className="chatbot-message-row chatbot-message-row--assistant"
                    key={message.id}
                  >
                    <div
                      className="chatbot-message-avatar"
                      aria-hidden="true"
                    >
                      <Bot size={19} strokeWidth={2.2} />
                    </div>

                    <div className="chatbot-message-group">
                      <div className="chatbot-message chatbot-message--assistant chatbot-message--error">
                        <p>{message.text}</p>
                      </div>
                    </div>
                  </div>
                );
              }

              return (
                <div
                  className="chatbot-message-row chatbot-message-row--assistant"
                  key={message.id}
                >
                  <div
                    className="chatbot-message-avatar"
                    aria-hidden="true"
                  >
                    <Bot size={19} strokeWidth={2.2} />
                  </div>

                  <div className="chatbot-message-group">
                    {renderAssistantResponse(message.response)}
                  </div>
                </div>
              );
            })}

            {isSending && (
              <div className="chatbot-message-row chatbot-message-row--assistant">
                <div
                  className="chatbot-message-avatar"
                  aria-hidden="true"
                >
                  <Bot size={19} strokeWidth={2.2} />
                </div>

                <div className="chatbot-message-group">
                  <div className="chatbot-message chatbot-message--assistant chatbot-thinking">
                    <LoaderCircle
                      size={17}
                      strokeWidth={2}
                      aria-hidden="true"
                    />
                    <span>Thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div
              className="chatbot-empty-space"
              aria-hidden="true"
            />
          </div>

          <div className="chatbot-suggestions">
            {suggestions.map((suggestion) => (
              <button
                type="button"
                key={suggestion}
                disabled={isSending}
                onClick={() => {
                  void sendMessage(suggestion);
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>

          <div className="chatbot-composer">
            <div className="chatbot-composer__field">
              <textarea
                ref={textareaRef}
                rows={1}
                value={input}
                maxLength={2000}
                placeholder="Type your message..."
                aria-label="Chatbot message"
                disabled={isSending}
                onChange={(event) => {
                  setInput(event.target.value);
                }}
                onKeyDown={handleKeyDown}
              />

              <button
                type="button"
                className="chatbot-send-button"
                aria-label="Send message"
                disabled={!input.trim() || isSending}
                onClick={() => {
                  void sendMessage();
                }}
              >
                {isSending ? (
                  <LoaderCircle
                    className="chatbot-send-button__loader"
                    size={18}
                    strokeWidth={2.2}
                  />
                ) : (
                  <span aria-hidden="true">➤</span>
                )}
              </button>
            </div>

            <div className="chatbot-powered">
              Powered by <strong>QuizApp AI</strong>
              <Sparkles
                size={13}
                strokeWidth={2}
                aria-hidden="true"
              />
            </div>
          </div>
        </section>
      )}

      {!isOpen && (
        <button
          type="button"
          className="chatbot-launcher"
          aria-label="Open QuizApp AI assistant"
          onClick={() => {
            setIsClosing(false);
            setIsOpen(true);
          }}
        >
          <MessageCircle size={27} strokeWidth={2.2} />
          <span
            className="chatbot-launcher__bot"
            aria-hidden="true"
          >
            <Bot size={16} strokeWidth={2.4} />
          </span>
        </button>
      )}
    </div>
  );
}

export default ChatbotWidget;
