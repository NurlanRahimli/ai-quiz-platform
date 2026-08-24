import {
    type ChangeEvent,
    type DragEvent,
    useRef,
    useState,
} from "react";
import { useNavigate } from "react-router-dom";

import axios from "axios";
import apiClient from "../../api/client";

import {
    Check,
    FileImage,
    FileText,
    ListChecks,
    ShieldCheck,
    Sparkles,
    Trash2,
    Trophy,
    Upload,
} from "lucide-react";


import "../../styles/pages/quizzes/ImportQuizPage.css";

const MAX_FILE_SIZE = 10 * 1024 * 1024;

const ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png"];

const ALLOWED_CONTENT_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
];

function formatFileSize(bytes: number) {
    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileExtension(filename: string) {
    const dotIndex = filename.lastIndexOf(".");

    if (dotIndex === -1) {
        return "";
    }

    return filename.slice(dotIndex).toLowerCase();
}


type AnswerSource =
    | "document"
    | "ai_inferred"
    | "unavailable";

interface ImportedAnswerChoice {
    text: string;
    is_correct: boolean;
}

interface ImportedQuestion {
    question_type:
    | "multiple_choice"
    | "written_answer"
    | "math_work";
    text: string;
    choices: ImportedAnswerChoice[];
    expected_answer: string | null;
    answer_source: AnswerSource;
    needs_review: boolean;
    review_reason: string | null;
}

interface ImportedQuiz {
    title: string | null;
    description: string | null;
    category: string;
    tags: string[];
    questions: ImportedQuestion[];
}


export default function ImportQuizPage() {
    const navigate = useNavigate();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [fileError, setFileError] = useState("");
    const [isDragging, setIsDragging] = useState(false);

    const [isProcessing, setIsProcessing] = useState(false);
    const [processingProgress, setProcessingProgress] = useState(0);

    const processingStage =
        processingProgress < 25
            ? 0
            : processingProgress < 55
                ? 1
                : processingProgress < 80
                    ? 2
                    : 3;

    const processingSteps = [
        "Uploading file",
        "Reading document",
        "Identifying questions & answers",
        "Structuring quiz",
    ];

    const estimatedSecondsLeft =
        processingProgress >= 100
            ? 0
            : Math.max(
                1,
                Math.ceil(((100 - processingProgress) / 100) * 20),
            );

    const validateAndSelectFile = (file: File) => {
        const extension = getFileExtension(file.name);

        if (
            !ALLOWED_EXTENSIONS.includes(extension) ||
            !ALLOWED_CONTENT_TYPES.includes(file.type)
        ) {
            setSelectedFile(null);
            setFileError(
                "Please upload a PDF, JPG, JPEG, or PNG file.",
            );
            return;
        }

        if (file.size === 0) {
            setSelectedFile(null);
            setFileError("The uploaded file cannot be empty.");
            return;
        }

        if (file.size > MAX_FILE_SIZE) {
            setSelectedFile(null);
            setFileError(
                "The uploaded file must be 10 MB or smaller.",
            );
            return;
        }

        setSelectedFile(file);
        setFileError("");
    };

    const handleChooseFile = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (
        event: ChangeEvent<HTMLInputElement>,
    ) => {
        const files = event.target.files;

        if (!files || files.length === 0) {
            return;
        }

        if (files.length > 1) {
            setSelectedFile(null);
            setFileError("Please upload only one file at a time.");
            event.target.value = "";
            return;
        }

        validateAndSelectFile(files[0]);
        event.target.value = "";
    };

    const handleDragOver = (
        event: DragEvent<HTMLDivElement>,
    ) => {
        event.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (
        event: DragEvent<HTMLDivElement>,
    ) => {
        event.preventDefault();
        setIsDragging(false);
    };

    const handleDrop = (
        event: DragEvent<HTMLDivElement>,
    ) => {
        event.preventDefault();
        setIsDragging(false);

        const files = event.dataTransfer.files;

        if (files.length === 0) {
            return;
        }

        if (files.length > 1) {
            setSelectedFile(null);
            setFileError("Please upload only one file at a time.");
            return;
        }

        validateAndSelectFile(files[0]);
    };

    const handleRemoveFile = () => {
        setSelectedFile(null);
        setFileError("");

        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };


    const handleImportQuiz = async () => {
        if (!selectedFile || isProcessing) {
            return;
        }

        setFileError("");
        setIsProcessing(true);
        setProcessingProgress(5);

        const progressInterval = window.setInterval(() => {
            setProcessingProgress((currentProgress) => {
                if (currentProgress >= 95) {
                    return 95;
                }

                if (currentProgress < 25) {
                    return Math.min(currentProgress + 4, 25);
                }

                if (currentProgress < 55) {
                    return Math.min(currentProgress + 3, 55);
                }

                if (currentProgress < 80) {
                    return Math.min(currentProgress + 2, 80);
                }

                return Math.min(currentProgress + 1, 95);
            });
        }, 700);

        const formData = new FormData();
        formData.append("file", selectedFile);

        try {
            const response = await apiClient.post<ImportedQuiz>(
                "/ai/import-quiz",
                formData,
                {
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                },
            );

            const importedQuiz = response.data;

            const importedDraft = {
                form: {
                    title: importedQuiz.title ?? "",
                    description: importedQuiz.description ?? "",
                    category: importedQuiz.category ?? "",
                    tags: importedQuiz.tags ?? [],
                    visibility: "unlisted",
                },
                questions: importedQuiz.questions.map((question) => ({
                    id: crypto.randomUUID(),
                    question_type: question.question_type,
                    text: question.text,
                    expected_answer: question.expected_answer ?? "",
                    choices: question.choices.map((choice) => ({
                        id: crypto.randomUUID(),
                        text: choice.text,
                        is_correct: choice.is_correct,
                    })),
                })),
                isAddingQuestion: false,
                newQuestionType: "multiple_choice",
                newQuestionText: "",
                newExpectedAnswer: "",
                newQuestionChoices: [
                    {
                        id: crypto.randomUUID(),
                        text: "",
                        is_correct: true,
                    },
                    {
                        id: crypto.randomUUID(),
                        text: "",
                        is_correct: false,
                    },
                ],
            };

            localStorage.setItem(
                "create-quiz-draft",
                JSON.stringify(importedDraft),
            );

            window.clearInterval(progressInterval);
            setProcessingProgress(100);

            await new Promise((resolve) => {
                window.setTimeout(resolve, 600);
            });

            navigate("/quizzes/new");
        } catch (error) {
            window.clearInterval(progressInterval);
            setProcessingProgress(0);
            if (axios.isAxiosError(error)) {
                const detail = error.response?.data?.detail;

                setFileError(
                    typeof detail === "string"
                        ? detail
                        : "Unable to import the quiz right now.",
                );
            } else {
                setFileError("Unable to import the quiz right now.");
            }
        } finally {
            window.clearInterval(progressInterval);
            setIsProcessing(false);
        }
    };

    return (
        <main className="import-quiz-page">
            <header className="import-quiz-page__header">
                <div
                    className="import-quiz-page__header-icon"
                    aria-hidden="true"
                >
                    <FileText size={31} strokeWidth={1.8} />
                    <Upload
                        className="import-quiz-page__header-upload-icon"
                        size={14}
                        strokeWidth={2.3}
                    />
                </div>

                <div>
                    <h1>Upload Quiz</h1>
                    <p>
                        Upload a PDF or image containing your quiz. We'll
                        extract the title, questions, answers, category, and
                        tags using AI.
                    </p>
                </div>
            </header>

            <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
                className="import-quiz-file-input"
                onChange={handleFileChange}
            />

            <section
                className={`import-quiz-dropzone ${isDragging
                    ? "import-quiz-dropzone--dragging"
                    : ""
                    }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                <div
                    className="import-quiz-dropzone__file-icon"
                    aria-hidden="true"
                >
                    {selectedFile?.type.startsWith("image/") ? (
                        <FileImage size={54} strokeWidth={1.55} />
                    ) : (
                        <FileText size={54} strokeWidth={1.55} />
                    )}

                    <span>
                        {selectedFile?.type.startsWith("image/")
                            ? "IMG"
                            : "PDF"}
                    </span>
                </div>

                <h2>Drag & drop your quiz here</h2>

                <p className="import-quiz-dropzone__or">or</p>

                <button
                    type="button"
                    className="import-quiz-dropzone__button"
                    onClick={handleChooseFile}
                >
                    <Upload size={17} strokeWidth={2} aria-hidden="true" />
                    Browse Files
                </button>

                <p className="import-quiz-dropzone__support">
                    Supports PDF, JPG, JPEG, and PNG files up to 10 MB
                </p>
            </section>

            {fileError && (
                <div className="import-quiz-file-error" role="alert">
                    {fileError}
                </div>
            )}

            <section className="import-quiz-process">
                <h2>Import Process</h2>

                <div className="import-quiz-process__steps">
                    <div className="import-quiz-process__step import-quiz-process__step--active">
                        <div className="import-quiz-process__number">1</div>
                        <strong>Upload File</strong>
                        <span>Add your quiz file</span>
                    </div>

                    <div
                        className="import-quiz-process__connector"
                        aria-hidden="true"
                    >
                        <span>→</span>
                    </div>

                    <div className="import-quiz-process__step">
                        <div className="import-quiz-process__number">2</div>
                        <strong>AI Processing</strong>
                        <span>Extract text & structure</span>
                    </div>

                    <div
                        className="import-quiz-process__connector"
                        aria-hidden="true"
                    >
                        <span>→</span>
                    </div>

                    <div className="import-quiz-process__step">
                        <div className="import-quiz-process__number">3</div>
                        <strong>Review Content</strong>
                        <span>Verify extracted data</span>
                    </div>

                    <div
                        className="import-quiz-process__connector"
                        aria-hidden="true"
                    >
                        <span>→</span>
                    </div>

                    <div className="import-quiz-process__step">
                        <div className="import-quiz-process__number">4</div>
                        <strong>Create Quiz</strong>
                        <span>Save to your quizzes</span>
                    </div>
                </div>
            </section>

            {selectedFile && (
                <section className="import-quiz-uploaded">
                    <h2>Uploaded File</h2>

                    <div className="import-quiz-selected-file">
                        <div className="import-quiz-selected-file__icon">
                            {selectedFile.type === "application/pdf" ? (
                                <FileText size={22} aria-hidden="true" />
                            ) : (
                                <FileImage size={22} aria-hidden="true" />
                            )}
                        </div>

                        <div className="import-quiz-selected-file__info">
                            <strong>{selectedFile.name}</strong>
                            <span>{formatFileSize(selectedFile.size)}</span>
                        </div>

                        <div className="import-quiz-selected-file__success">
                            <Check size={17} aria-hidden="true" />
                            Uploaded successfully
                        </div>

                        <button
                            type="button"
                            className="import-quiz-selected-file__remove"
                            onClick={handleRemoveFile}
                            aria-label="Remove selected file"
                        >
                            <Trash2 size={18} aria-hidden="true" />
                        </button>
                    </div>

                    <div className="import-quiz-uploaded__message">
                        <Check size={17} aria-hidden="true" />
                        <span>
                            File uploaded! It's ready for AI processing.
                        </span>
                    </div>
                </section>
            )}

            <section className="import-quiz-processing">
                <div className="import-quiz-processing__heading">
                    <div>
                        <h2>AI Processing</h2>
                        <Sparkles size={17} aria-hidden="true" />
                    </div>

                    <span>
                        {isProcessing
                            ? processingProgress >= 100
                                ? "Complete"
                                : `About ${estimatedSecondsLeft}s left`
                            : "Ready when you are"}
                    </span>
                </div>

                <div className="import-quiz-processing__content">
                    <div className="import-quiz-processing__status">
                        <div
                            className="import-quiz-processing__circle"
                            style={{
                                background: `conic-gradient(
            var(--color-primary-500) ${processingProgress * 3.6}deg,
            var(--color-border) 0deg
        )`,
                            }}
                        >
                            <strong>
                                {isProcessing ? processingProgress : 0}%
                            </strong>
                        </div>

                        <div className="import-quiz-processing__description">
                            <strong>Extracting quiz content</strong>
                            <span>
                                AI will analyze your file and structure the quiz.
                            </span>

                            <div className="import-quiz-processing__tasks">
                                {processingSteps.map((step, index) => {
                                    const isComplete =
                                        processingProgress >= 100 || index < processingStage;

                                    const isActive =
                                        isProcessing &&
                                        processingProgress < 100 &&
                                        index === processingStage;

                                    return (
                                        <div
                                            key={step}
                                            className={`import-quiz-processing__task ${isComplete
                                                ? "import-quiz-processing__task--complete"
                                                : ""
                                                } ${isActive
                                                    ? "import-quiz-processing__task--active"
                                                    : ""
                                                }`}
                                        >
                                            <div className="import-quiz-processing__task-icon">
                                                {isComplete ? (
                                                    <Check size={15} strokeWidth={2.5} />
                                                ) : (
                                                    <span>{index + 1}</span>
                                                )}
                                            </div>

                                            <span>{step}</span>

                                            {isActive && (
                                                <span className="import-quiz-processing__task-status">
                                                    Processing...
                                                </span>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="import-quiz-processing__extract">
                    <h3>What we'll extract</h3>

                    <div className="import-quiz-processing__extract-grid">
                        <div className="import-quiz-extract-card">
                            <div className="import-quiz-extract-card__icon">
                                <FileText size={19} />
                            </div>
                            <div>
                                <strong>Quiz Title</strong>
                                <span>
                                    We'll detect the title when one is provided.
                                </span>
                            </div>
                        </div>

                        <div className="import-quiz-extract-card">
                            <div className="import-quiz-extract-card__icon">
                                <ListChecks size={19} />
                            </div>
                            <div>
                                <strong>Questions</strong>
                                <span>
                                    Up to 30 questions will be identified.
                                </span>
                            </div>
                        </div>

                        <div className="import-quiz-extract-card">
                            <div className="import-quiz-extract-card__icon">
                                <Check size={19} />
                            </div>
                            <div>
                                <strong>Answer Options</strong>
                                <span>
                                    Multiple-choice options will be extracted.
                                </span>
                            </div>
                        </div>

                        <div className="import-quiz-extract-card">
                            <div className="import-quiz-extract-card__icon">
                                <Trophy size={19} />
                            </div>
                            <div>
                                <strong>Correct Answers</strong>
                                <span>
                                    AI will detect or infer expected answers.
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section className="import-quiz-security">
                <ShieldCheck size={27} strokeWidth={1.8} aria-hidden="true" />

                <div>
                    <strong>Your data is secure</strong>
                    <p>
                        Your file is processed only to extract the content
                        needed to prepare your quiz.
                    </p>
                </div>
            </section>

            <div className="import-quiz-actions">
                <button
                    type="button"
                    className="import-quiz-actions__cancel"
                    onClick={handleRemoveFile}
                    disabled={!selectedFile || isProcessing}
                >
                    Cancel Upload
                </button>

                <button
                    type="button"
                    className="import-quiz-actions__continue"
                    onClick={handleImportQuiz}
                    disabled={!selectedFile || isProcessing}
                >
                    {isProcessing ? "Processing..." : "Continue to Review"}
                    {!isProcessing && <span aria-hidden="true">→</span>}
                </button>
            </div>
        </main>
    );
}
