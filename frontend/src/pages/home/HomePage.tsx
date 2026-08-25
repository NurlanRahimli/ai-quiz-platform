import {
  ArrowRight,
  Bookmark,
  Bot,
  BrainCircuit,
  Check,
  FilePlus2,
  FileText,
  FileUp,
  Lightbulb,
  ListChecks,
  MessageCircle,
  Send,
  Sparkles,
  Star,
  Tags,
  TrendingUp,
  Trophy,
  WandSparkles,
} from "lucide-react";
import type { MouseEvent } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../auth/useAuth";
import QuizIcon from "../../components/quizzes/QuizIcon";
import "../../styles/pages/home/HomePage.css";

const featuredQuizzes = [
  {
    id: "javascript-fundamentals",
    title: "JavaScript Fundamentals",
    category: "Programming",
    icon: "code-2",
    questionCount: 20,
    attempts: "1.2k",
    creator: "Alex Morgan",
  },
  {
    id: "world-history",
    title: "World History",
    category: "History",
    icon: "landmark",
    questionCount: 15,
    attempts: "980",
    creator: "Sarah Kim",
  },
  {
    id: "biology-basics",
    title: "Biology Basics",
    category: "Science",
    icon: "microscope",
    questionCount: 25,
    attempts: "2.1k",
    creator: "Daniel Lee",
  },
  {
    id: "algebra-practice",
    title: "Algebra Practice",
    category: "Mathematics",
    icon: "calculator",
    questionCount: 18,
    attempts: "1.5k",
    creator: "Emily Chen",
  },
];

export default function HomePage() {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuth();
  const handleHeroVisualMove = (event: MouseEvent<HTMLDivElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();

    const x = (event.clientX - bounds.left) / bounds.width - 0.5;
    const y = (event.clientY - bounds.top) / bounds.height - 0.5;

    event.currentTarget.style.setProperty("--hero-parallax-x", `${x * -22}px`);
    event.currentTarget.style.setProperty("--hero-parallax-y", `${y * -16}px`);
    event.currentTarget.style.setProperty("--hero-rotate-y", `${x * -2.5}deg`);
    event.currentTarget.style.setProperty("--hero-rotate-x", `${y * 2}deg`);
  };

  const handleHeroVisualLeave = (event: MouseEvent<HTMLDivElement>) => {
    event.currentTarget.style.setProperty("--hero-parallax-x", "0px");
    event.currentTarget.style.setProperty("--hero-parallax-y", "0px");
    event.currentTarget.style.setProperty("--hero-rotate-y", "0deg");
    event.currentTarget.style.setProperty("--hero-rotate-x", "0deg");
  };

  const goToCreateQuiz = () => {
    navigate(isAuthenticated ? "/quizzes/new" : "/login");
  };

  const goToImportQuiz = () => {
    navigate(isAuthenticated ? "/import-quiz" : "/login");
  };

  return (
    <main className="home-page">
      <header className="home-navbar">
        <button
          type="button"
          className="home-brand"
          onClick={() => navigate("/")}
          aria-label="QuizApp home"
        >
          <span className="home-brand__icon">
            <BrainCircuit size={23} aria-hidden="true" />
          </span>
          <span>QuizApp</span>
        </button>

        <nav className="home-navbar__links" aria-label="Home navigation">
          <a href="#features">Features</a>
          <a href="#ai">AI</a>
          <a href="#how-it-works">How It Works</a>
          <button type="button" onClick={() => navigate("/discover")}>
            Explore Quizzes
          </button>
        </nav>

        <div className="home-navbar__actions">
          {!isLoading && isAuthenticated ? (
            <button
              type="button"
              className="home-nav-button home-nav-button--primary"
              onClick={() => navigate("/dashboard")}
            >
              Dashboard
            </button>
          ) : (
            <>
              <button
                type="button"
                className="home-nav-button home-nav-button--secondary"
                onClick={() => navigate("/login")}
              >
                Log in
              </button>

              <button
                type="button"
                className="home-nav-button home-nav-button--primary"
                onClick={() => navigate("/register")}
              >
                Sign up
              </button>
            </>
          )}
        </div>
      </header>

      <section className="home-hero">
        <div className="home-hero__content">
          <h1>
            Learn smarter.
            <span>Create faster.</span>
            Understand your progress.
          </h1>

          <p>
            Create quizzes manually or from documents, practice with the
            community, and use AI to understand your results.
          </p>

          <div className="home-hero__actions">
            <button
              type="button"
              className="home-button home-button--primary"
              onClick={goToCreateQuiz}
            >
              <Sparkles size={18} aria-hidden="true" />
              Create Quiz
              <ArrowRight size={18} aria-hidden="true" />
            </button>

            <button
              type="button"
              className="home-button home-button--secondary"
              onClick={() => navigate("/discover")}
            >
              Explore Quizzes
              <ArrowRight size={18} aria-hidden="true" />
            </button>
          </div>

          <button
            type="button"
            className="home-hero__upload"
            onClick={goToImportQuiz}
          >
            <FileUp size={18} aria-hidden="true" />
            Upload with OCR
          </button>
        </div>

        <div
          className="home-hero__visual"
          aria-hidden="true"
          onMouseMove={handleHeroVisualMove}
          onMouseLeave={handleHeroVisualLeave}
        >
          <div className="home-hero__visual-motion">
          <div className="home-visual-orbit" />

          <div className="home-visual-card home-visual-card--brain">
            <BrainCircuit size={78} strokeWidth={1.6} />
          </div>

          <div className="home-visual-card home-visual-card--quiz">
            <strong>Q.</strong>
            <span />
            <span />
            <span />
            <span />
            <i>✓</i>
          </div>

          <div className="home-visual-card home-visual-card--chart">
            <svg viewBox="0 0 150 90">
              <polyline
                points="12,70 36,55 57,63 82,38 104,51 137,21"
                fill="none"
                stroke="currentColor"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="137" cy="21" r="6" fill="currentColor" />
            </svg>
          </div>

          <div className="home-visual-document">
            <FileUp size={34} />
            <strong>PDF</strong>
          </div>

          <span className="home-sparkle home-sparkle--one">✦</span>
          <span className="home-sparkle home-sparkle--two">✦</span>
          <span className="home-sparkle home-sparkle--three">✦</span>
          </div>
        </div>
      </section>

      <section className="home-featured" aria-labelledby="featured-quizzes-title">
        <div className="home-section-heading">
          <h2 id="featured-quizzes-title">
            <Star size={21} aria-hidden="true" />
            Featured Quizzes
          </h2>

          <button
            type="button"
            className="home-section-link"
            onClick={() => navigate("/discover")}
          >
            Explore all quizzes
            <ArrowRight size={16} aria-hidden="true" />
          </button>
        </div>

        <div className="home-featured-grid">
          {featuredQuizzes.map((quiz) => (
            <article
              key={quiz.id}
              className="home-featured-card"
            >
              <div className="home-featured-card__icon">
                <QuizIcon
                  name={quiz.icon}
                  size={28}
                  strokeWidth={1.9}
                />
              </div>

              <div className="home-featured-card__body">
                <h3>{quiz.title}</h3>

                <p className="home-featured-card__meta">
                  <span>{quiz.category}</span>
                  <i aria-hidden="true">•</i>
                  <span>{quiz.questionCount} Questions</span>
                </p>

                <p className="home-featured-card__attempts">
                  <Star size={14} aria-hidden="true" />
                  {quiz.attempts} attempts
                </p>
              </div>

              <div className="home-featured-card__footer">
                <span
                  className="home-featured-card__avatar"
                  aria-hidden="true"
                >
                  {quiz.creator.charAt(0)}
                </span>

                <span className="home-featured-card__creator">
                  by {quiz.creator}
                </span>

                <Bookmark
                  className="home-featured-card__bookmark"
                  size={18}
                  aria-hidden="true"
                />
              </div>
            </article>
          ))}
        </div>
      </section>

      <section
        className="home-create-section"
        id="features"
        aria-labelledby="home-create-title"
      >
        <div className="home-create-heading">
          <h2 id="home-create-title">Create quizzes your way</h2>
          <p>
            Build from scratch or turn your existing documents into quizzes.
          </p>
        </div>

        <div className="home-create-grid">
          <article className="home-create-card">
            <div className="home-create-card__content">
              <div className="home-create-card__icon">
                <FilePlus2 size={27} aria-hidden="true" />
              </div>

              <h3>Build Manually</h3>

              <p>
                Create questions, answers, categories, and tags with full
                control over your quiz.
              </p>

              <div className="home-create-card__features">
                <span>
                  <ListChecks size={15} aria-hidden="true" />
                  Multiple question types
                </span>

                <span>
                  <Tags size={15} aria-hidden="true" />
                  Categories &amp; tags
                </span>
              </div>

              <button
                type="button"
                className="home-create-card__action"
                onClick={goToCreateQuiz}
              >
                Start building
                <ArrowRight size={16} aria-hidden="true" />
              </button>
            </div>

            <div
              className="home-create-card__preview home-create-manual-preview"
              aria-hidden="true"
            >
              <div className="home-manual-window">
                <div className="home-manual-window__top">
                  <span />
                  <span />
                  <span />
                </div>

                <div className="home-manual-window__body">
                  <span className="home-manual-label">Question 1</span>
                  <div className="home-manual-question" />

                  <div className="home-manual-answer">
                    <i>A</i>
                    <span />
                  </div>

                  <div className="home-manual-answer home-manual-answer--selected">
                    <i>B</i>
                    <span />
                    <strong>✓</strong>
                  </div>

                  <div className="home-manual-answer">
                    <i>C</i>
                    <span />
                  </div>
                </div>
              </div>
            </div>
          </article>

          <article className="home-create-card">
            <div className="home-create-card__content">
              <div className="home-create-card__icon">
                <FileUp size={27} aria-hidden="true" />
              </div>

              <h3>Import with OCR</h3>

              <p>
                Upload a PDF or image and transform your document into an
                editable quiz.
              </p>

              <div className="home-create-card__features">
                <span>
                  <FileText size={15} aria-hidden="true" />
                  PDF, JPG &amp; PNG
                </span>

                <span>
                  <WandSparkles size={15} aria-hidden="true" />
                  Automatic extraction
                </span>
              </div>

              <button
                type="button"
                className="home-create-card__action"
                onClick={goToImportQuiz}
              >
                Import document
                <ArrowRight size={16} aria-hidden="true" />
              </button>
            </div>

            <div
              className="home-create-card__preview home-create-ocr-preview"
              aria-hidden="true"
            >
              <div className="home-ocr-document">
                <div className="home-ocr-document__corner" />

                <div className="home-ocr-document__header">
                  <FileText size={23} />
                  <span>QUIZ.PDF</span>
                </div>

                <div className="home-ocr-line home-ocr-line--wide" />
                <div className="home-ocr-line" />
                <div className="home-ocr-line home-ocr-line--short" />

                <div className="home-ocr-scan">
                  <span />
                </div>
              </div>

              <div className="home-ocr-arrow">
                <ArrowRight size={24} />
              </div>

              <div className="home-ocr-result">
                <Sparkles size={20} />
                <strong>Quiz</strong>
                <span>Generated</span>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section
        className="home-ai-section"
        id="ai"
        aria-labelledby="home-ai-title"
      >
        <div className="home-ai-heading">
          <span className="home-ai-heading__eyebrow">
            <Sparkles size={14} aria-hidden="true" />
            Powered by AI
          </span>

          <h2 id="home-ai-title">
            Don&apos;t just see your score.
            <span>Understand it.</span>
          </h2>

          <p>
            Turn every quiz attempt into a learning opportunity with
            explanations, intelligent assistance, and smarter quiz creation.
          </p>
        </div>

        <div className="home-ai-grid">
          <article className="home-ai-feature home-ai-feature--explanation">
            <div className="home-ai-feature__copy">
              <span className="home-ai-feature__icon">
                <Lightbulb size={22} aria-hidden="true" />
              </span>

              <h3>Understand your mistakes</h3>

              <p>
                Get clear AI-powered explanations for incorrect answers and
                learn why the correct answer makes sense.
              </p>
            </div>

            <div className="home-ai-explanation-preview" aria-hidden="true">
              <div className="home-ai-explanation-preview__question">
                <span>QUESTION 04</span>
                <strong>What does HTTP stand for?</strong>
              </div>

              <div className="home-ai-answer home-ai-answer--wrong">
                <span className="home-ai-answer__marker">×</span>
                <div>
                  <small>Your answer</small>
                  <strong>High Transfer Text Protocol</strong>
                </div>
              </div>

              <div className="home-ai-answer home-ai-answer--correct">
                <span className="home-ai-answer__marker">
                  <Check size={13} />
                </span>
                <div>
                  <small>Correct answer</small>
                  <strong>Hypertext Transfer Protocol</strong>
                </div>
              </div>

              <div className="home-ai-explanation">
                <div>
                  <Sparkles size={13} />
                  <strong>AI Explanation</strong>
                </div>

                <p>
                  HTTP is the protocol used to transfer hypertext documents
                  between web servers and browsers.
                </p>
              </div>
            </div>
          </article>

          <article className="home-ai-feature home-ai-feature--chat">
            <div className="home-ai-feature__copy">
              <span className="home-ai-feature__icon">
                <MessageCircle size={22} aria-hidden="true" />
              </span>

              <h3>Ask when you&apos;re stuck</h3>

              <p>
                Use an AI learning assistant to ask questions and understand
                concepts without leaving your study flow.
              </p>
            </div>

            <div className="home-ai-chat-preview" aria-hidden="true">
              <div className="home-ai-chat-preview__header">
                <span className="home-ai-chat-preview__bot">
                  <Bot size={16} />
                </span>

                <div>
                  <strong>QuizApp AI</strong>
                  <small>Learning assistant</small>
                </div>

                <i />
              </div>

              <div className="home-ai-chat-preview__messages">
                <div className="home-ai-message home-ai-message--user">
                  Why is this answer incorrect?
                </div>

                <div className="home-ai-message home-ai-message--assistant">
                  <span>
                    <Sparkles size={12} />
                  </span>
                  <p>
                    The key difference is that HTTP describes how information
                    is transferred across the web.
                  </p>
                </div>
              </div>

              <div className="home-ai-chat-preview__input">
                <span>Ask a follow-up...</span>
                <i>
                  <Send size={12} />
                </i>
              </div>
            </div>
          </article>

          <article className="home-ai-feature home-ai-feature--generate">
            <div className="home-ai-feature__copy">
              <span className="home-ai-feature__icon">
                <WandSparkles size={22} aria-hidden="true" />
              </span>

              <h3>Create in seconds</h3>

              <p>
                Enter a topic and let AI prepare a quiz structure you can
                review, edit, and make your own.
              </p>
            </div>

            <div className="home-ai-generator-preview" aria-hidden="true">
              <div className="home-ai-generator-preview__label">
                What should your quiz be about?
              </div>

              <div className="home-ai-generator-preview__input">
                <span>Introduction to machine learning</span>
                <i>
                  <Sparkles size={13} />
                </i>
              </div>

              <div className="home-ai-generator-options">
                <span>10 questions</span>
                <span>Medium</span>
              </div>

              <div className="home-ai-generator-button">
                <WandSparkles size={14} />
                Generate Quiz
              </div>

              <div className="home-ai-generator-status">
                <span>
                  <Check size={11} />
                </span>
                Quiz ready to review
              </div>
            </div>
          </article>
        </div>
      </section>

      <section
        className="home-progress-section"
        id="how-it-works"
        aria-labelledby="home-progress-title"
      >
        <div className="home-progress-copy">
          <span className="home-progress-eyebrow">
            <TrendingUp size={14} aria-hidden="true" />
            Track your progress
          </span>

          <h2 id="home-progress-title">
            See your learning
            <span>clearly.</span>
          </h2>

          <p>
            Understand how you&apos;re improving with simple performance
            insights that show your scores, activity, and strongest subjects.
          </p>

          <div className="home-progress-points">
            <div>
              <span>
                <Check size={13} aria-hidden="true" />
              </span>
              Track your average quiz score
            </div>

            <div>
              <span>
                <Check size={13} aria-hidden="true" />
              </span>
              Follow your performance over time
            </div>

            <div>
              <span>
                <Check size={13} aria-hidden="true" />
              </span>
              Discover your strongest categories
            </div>
          </div>
        </div>

        <div className="home-progress-dashboard" aria-hidden="true">
          <div className="home-progress-dashboard__top">
            <div>
              <span className="home-progress-dashboard__eyebrow">
                YOUR PROGRESS
              </span>
              <strong>Learning overview</strong>
            </div>

            <span className="home-progress-dashboard__period">
              Last 30 days
            </span>
          </div>

          <div className="home-progress-stats">
            <div className="home-progress-stat">
              <span>Average Score</span>

              <div>
                <strong>84%</strong>
                <small>
                  <TrendingUp size={10} />
                  6.4%
                </small>
              </div>
            </div>

            <div className="home-progress-stat">
              <span>Quizzes Taken</span>

              <div>
                <strong>28</strong>
                <small>
                  <TrendingUp size={10} />
                  12%
                </small>
              </div>
            </div>

            <div className="home-progress-stat">
              <span>Best Category</span>

              <div>
                <strong className="home-progress-stat__category">
                  Programming
                </strong>

                <small className="home-progress-stat__trophy">
                  <Trophy size={11} />
                </small>
              </div>
            </div>
          </div>

          <div className="home-progress-main">
            <div className="home-progress-chart-card">
              <div className="home-progress-card-heading">
                <div>
                  <strong>Performance</strong>
                  <span>Average score over time</span>
                </div>

                <span>84%</span>
              </div>

              <div className="home-progress-chart">
                <div className="home-progress-chart__grid">
                  <span />
                  <span />
                  <span />
                  <span />
                </div>

                <svg viewBox="0 0 440 150" preserveAspectRatio="none">
                  <defs>
                    <linearGradient
                      id="homeProgressArea"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopColor="#8b5cf6"
                        stopOpacity="0.3"
                      />
                      <stop
                        offset="100%"
                        stopColor="#8b5cf6"
                        stopOpacity="0"
                      />
                    </linearGradient>
                  </defs>

                  <path
                    d="M0 118 C35 105, 55 112, 85 93 C115 75, 135 89, 165 70 C195 50, 215 72, 245 56 C275 40, 295 51, 325 35 C355 20, 385 33, 440 15 L440 150 L0 150 Z"
                    fill="url(#homeProgressArea)"
                  />

                  <path
                    d="M0 118 C35 105, 55 112, 85 93 C115 75, 135 89, 165 70 C195 50, 215 72, 245 56 C275 40, 295 51, 325 35 C355 20, 385 33, 440 15"
                    fill="none"
                    stroke="#9b5cf6"
                    strokeWidth="3"
                    strokeLinecap="round"
                  />

                  <circle cx="440" cy="15" r="5" fill="#b56cff" />
                </svg>

                <div className="home-progress-chart__labels">
                  <span>Week 1</span>
                  <span>Week 2</span>
                  <span>Week 3</span>
                  <span>Week 4</span>
                </div>
              </div>
            </div>

            <div className="home-progress-categories">
              <div className="home-progress-card-heading">
                <div>
                  <strong>Top Categories</strong>
                  <span>Your strongest subjects</span>
                </div>
              </div>

              <div className="home-progress-category">
                <div>
                  <span>Programming</span>
                  <strong>92%</strong>
                </div>

                <i>
                  <span style={{ width: "92%" }} />
                </i>
              </div>

              <div className="home-progress-category">
                <div>
                  <span>Science</span>
                  <strong>86%</strong>
                </div>

                <i>
                  <span style={{ width: "86%" }} />
                </i>
              </div>

              <div className="home-progress-category">
                <div>
                  <span>Mathematics</span>
                  <strong>78%</strong>
                </div>

                <i>
                  <span style={{ width: "78%" }} />
                </i>
              </div>

              <div className="home-progress-category">
                <div>
                  <span>History</span>
                  <strong>74%</strong>
                </div>

                <i>
                  <span style={{ width: "74%" }} />
                </i>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section
        className="home-final-cta"
        aria-labelledby="home-final-cta-title"
      >
        <div className="home-final-cta__glow home-final-cta__glow--one" />
        <div className="home-final-cta__glow home-final-cta__glow--two" />

        <span
          className="home-final-cta__sparkle home-final-cta__sparkle--one"
          aria-hidden="true"
        >
          ✦
        </span>

        <span
          className="home-final-cta__sparkle home-final-cta__sparkle--two"
          aria-hidden="true"
        >
          ✦
        </span>

        <span
          className="home-final-cta__sparkle home-final-cta__sparkle--three"
          aria-hidden="true"
        >
          ✦
        </span>

        <div className="home-final-cta__content">
          <span className="home-final-cta__icon">
            <BrainCircuit size={30} aria-hidden="true" />
          </span>

          <h2 id="home-final-cta-title">
            Ready to learn smarter?
          </h2>

          <p>
            Create your first quiz, explore what others are learning, and turn
            every result into progress.
          </p>

          <div className="home-final-cta__actions">
            <button
              type="button"
              className="home-final-cta__button home-final-cta__button--primary"
              onClick={goToCreateQuiz}
            >
              <Sparkles size={17} aria-hidden="true" />
              Create Your First Quiz
              <ArrowRight size={17} aria-hidden="true" />
            </button>

            <button
              type="button"
              className="home-final-cta__button home-final-cta__button--secondary"
              onClick={() => navigate("/discover")}
            >
              Explore Quizzes
            </button>
          </div>

          {!isLoading && !isAuthenticated && (
            <span className="home-final-cta__note">
              Free to get started
            </span>
          )}
        </div>
      </section>
    </main>
  );
}
