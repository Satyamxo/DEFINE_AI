

import { useEffect, useMemo, useRef, useState } from "react";
import { askRepositoryQuestion } from "../api";


const chatCache = new Map();

function loadCachedMessages(repositoryName) {
    if (!repositoryName) {
        return [];
    }

    return (chatCache.get(repositoryName) || []).map((message) => ({
        ...message,
        animate: false,
    }));
}

const SUGGESTIONS = [
    "What is the main entry point?",
    "Explain the overall architecture.",
    "How does the application process input?",
    "Which files have the most dependencies?",
    "Summarize what each top-level folder does.",
    "Where is error handling implemented?",
];

// -----------------------------------------------
// Small icon helper (UI only)
// -----------------------------------------------

const ICONS = {
    expand: [
        "M8 3H5a2 2 0 00-2 2v3",
        "M21 8V5a2 2 0 00-2-2h-3",
        "M3 16v3a2 2 0 002 2h3",
        "M16 21h3a2 2 0 002-2v-3",
    ],
    collapse: [
        "M8 3v3a2 2 0 01-2 2H3",
        "M21 8h-3a2 2 0 01-2-2V3",
        "M3 16h3a2 2 0 012 2v3",
        "M16 21v-3a2 2 0 012-2h3",
    ],
    copy: ["M9 9h11v11H9z", "M5 15V5a2 2 0 012-2h10"],
    check: ["M5 13l4 4L19 7"],
    refresh: [
        "M3 12a9 9 0 0115-6.7L21 8",
        "M21 3v5h-5",
        "M21 12a9 9 0 01-15 6.7L3 16",
        "M3 21v-5h5",
    ],
    plus: ["M12 5v14", "M5 12h14"],
    close: ["M6 6l12 12", "M18 6L6 18"],
    send: ["M22 2L11 13", "M22 2l-7 20-4-9-9-4z"],
    stop: ["M7 7h10v10H7z"],
    sparkle: ["M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"],
    file: ["M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z", "M14 3v5h5"],
};

function Icon({ name, className = "h-4 w-4" }) {
    return (
        <svg
            viewBox="0 0 24 24"
            className={className}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            {ICONS[name].map((d) => (
                <path key={d} d={d} />
            ))}
        </svg>
    );
}

// -----------------------------------------------
// Lightweight Markdown renderer (no dependencies)
// Supports: code blocks, headings, lists, inline code, bold
// -----------------------------------------------

function renderInline(text) {
    return text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).map((part, index) => {
        if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
            return (
                <code
                    key={index}
                    className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-[0.85em] text-cyan-200"
                >
                    {part.slice(1, -1)}
                </code>
            );
        }

        if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
            return (
                <strong key={index} className="font-semibold text-white">
                    {part.slice(2, -2)}
                </strong>
            );
        }

        return part;
    });
}

const BULLET = /^\s*[-*]\s+/;
const NUMBERED = /^\s*\d+[.)]\s+/;
const HEADING = /^(#{1,3})\s+(.*)/;

function parseBlocks(text) {
    const lines = text.split("\n");
    const blocks = [];
    let i = 0;

    while (i < lines.length) {
        const line = lines[i];

        const fence = line.match(/^```(\w*)/);

        if (fence) {
            const code = [];
            i++;

            while (i < lines.length && !lines[i].startsWith("```")) {
                code.push(lines[i]);
                i++;
            }

            i++;
            blocks.push({ type: "code", lang: fence[1], text: code.join("\n") });
            continue;
        }

        const heading = line.match(HEADING);

        if (heading) {
            blocks.push({
                type: "heading",
                level: heading[1].length,
                text: heading[2],
            });
            i++;
            continue;
        }

        if (BULLET.test(line)) {
            const items = [];

            while (i < lines.length && BULLET.test(lines[i])) {
                items.push(lines[i].replace(BULLET, ""));
                i++;
            }

            blocks.push({ type: "ul", items });
            continue;
        }

        if (NUMBERED.test(line)) {
            const items = [];

            while (i < lines.length && NUMBERED.test(lines[i])) {
                items.push(lines[i].replace(NUMBERED, ""));
                i++;
            }

            blocks.push({ type: "ol", items });
            continue;
        }

        if (line.trim() === "") {
            i++;
            continue;
        }

        const paragraph = [];

        while (
            i < lines.length &&
            lines[i].trim() !== "" &&
            !lines[i].startsWith("```") &&
            !HEADING.test(lines[i]) &&
            !BULLET.test(lines[i]) &&
            !NUMBERED.test(lines[i])
        ) {
            paragraph.push(lines[i]);
            i++;
        }

        blocks.push({ type: "p", text: paragraph.join("\n") });
    }

    return blocks;
}

function CodeBlock({ lang, text }) {
    const [copied, setCopied] = useState(false);

    async function handleCopy() {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        } catch (copyError) {
            console.error("Failed to copy code:", copyError);
        }
    }

    return (
        <div className="my-3 overflow-hidden rounded-xl border border-white/10 bg-[#080a12]">
            <div className="flex items-center justify-between border-b border-white/10 px-3 py-1.5">
                <span className="text-xs text-gray-500">
                    {lang || "code"}
                </span>

                <button
                    type="button"
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-gray-400 transition hover:bg-white/10 hover:text-white"
                >
                    <Icon name={copied ? "check" : "copy"} className="h-3.5 w-3.5" />
                    {copied ? "Copied" : "Copy"}
                </button>
            </div>

            <pre className="overflow-x-auto p-3 font-mono text-[13px] leading-6 text-gray-200">
                <code>{text}</code>
            </pre>
        </div>
    );
}

function Markdown({ text }) {
    const blocks = useMemo(() => parseBlocks(text), [text]);

    return (
        <div className="space-y-3 break-words leading-7">
            {blocks.map((block, index) => {
                switch (block.type) {
                    case "code":
                        return (
                            <CodeBlock
                                key={index}
                                lang={block.lang}
                                text={block.text}
                            />
                        );

                    case "heading":
                        return (
                            <h4
                                key={index}
                                className={`da-display font-semibold text-white ${
                                    block.level === 1
                                        ? "text-lg"
                                        : block.level === 2
                                        ? "text-base"
                                        : "text-sm"
                                }`}
                            >
                                {renderInline(block.text)}
                            </h4>
                        );

                    case "ul":
                        return (
                            <ul
                                key={index}
                                className="list-disc space-y-1 pl-5 marker:text-violet-400"
                            >
                                {block.items.map((item, itemIndex) => (
                                    <li key={itemIndex}>{renderInline(item)}</li>
                                ))}
                            </ul>
                        );

                    case "ol":
                        return (
                            <ol
                                key={index}
                                className="list-decimal space-y-1 pl-5 marker:text-cyan-400"
                            >
                                {block.items.map((item, itemIndex) => (
                                    <li key={itemIndex}>{renderInline(item)}</li>
                                ))}
                            </ol>
                        );

                    default:
                        return (
                            <p key={index} className="whitespace-pre-wrap">
                                {renderInline(block.text)}
                            </p>
                        );
                }
            })}
        </div>
    );
}

// Reveals a new answer progressively, like a streaming reply.
function AnswerBody({ text, animate, onProgress }) {
    const [shown, setShown] = useState(animate ? 0 : text.length);

    useEffect(() => {
        if (!animate) {
            setShown(text.length);
            return undefined;
        }

        let current = 0;
        const step = Math.max(3, Math.ceil(text.length / 150));

        const timer = setInterval(() => {
            current = Math.min(text.length, current + step);
            setShown(current);

            if (onProgress) {
                onProgress();
            }

            if (current >= text.length) {
                clearInterval(timer);
            }
        }, 16);

        return () => clearInterval(timer);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [text, animate]);

    return <Markdown text={text.slice(0, shown)} />;
}

function Avatar() {
    return (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-cyan-400 shadow-lg shadow-violet-500/30">
            <Icon name="sparkle" className="h-4 w-4 text-white" />
        </div>
    );
}

function IconButton({ label, onClick, children, className = "" }) {
    return (
        <button
            type="button"
            onClick={onClick}
            title={label}
            aria-label={label}
            className={`flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 transition hover:bg-white/10 hover:text-white ${className}`}
        >
            {children}
        </button>
    );
}

function RepositoryChat({
    repositoryName,
    onViewSource,
    onClose,
}) {
    const [messages, setMessages] = useState(() =>
        loadCachedMessages(repositoryName)
    );
    const [question, setQuestion] = useState("");
    const [isAsking, setIsAsking] = useState(false);
    const [error, setError] = useState(null);
    const [fullscreen, setFullscreen] = useState(false);
    const [copiedIndex, setCopiedIndex] = useState(null);

    // UI helpers
    const bottomRef = useRef(null);
    const textareaRef = useRef(null);

    // Lets us ignore answers that are no longer wanted
    // (stopped, cleared, or repository changed).
    const requestIdRef = useRef(0);

    // Replace messages and remember them for this repository.
    function updateMessages(updater) {
        setMessages((previousMessages) => {
            const nextMessages = updater(previousMessages);

            if (repositoryName) {
                chatCache.set(repositoryName, nextMessages);
            }

            return nextMessages;
        });
    }

    // Clear the conversation when the repository changes.
    useEffect(() => {
        requestIdRef.current += 1;

        setMessages(loadCachedMessages(repositoryName));
        setQuestion("");
        setError(null);
        setIsAsking(false);
    }, [repositoryName]);

    // Scroll to the latest message.
    function scrollToBottom() {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }

    useEffect(() => {
        scrollToBottom();
    }, [messages, isAsking, error]);

    // Auto-grow the question box.
    useEffect(() => {
        const textarea = textareaRef.current;

        if (!textarea) {
            return;
        }

        textarea.style.height = "auto";
        textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }, [question, fullscreen]);

    // Ask the backend and add the answer.
    async function runQuery(trimmedQuestion) {
        const requestId = ++requestIdRef.current;

        setError(null);
        setIsAsking(true);

        try {
            const result = await askRepositoryQuestion(
                repositoryName,
                trimmedQuestion,
                5
            );

            if (requestId !== requestIdRef.current) {
                return;
            }

            updateMessages((previousMessages) => [
                ...previousMessages,
                {
                    role: "assistant",
                    content: result.answer,
                    sources: result.sources || [],
                    animate: true,
                },
            ]);
        } catch (requestError) {
            if (requestId !== requestIdRef.current) {
                return;
            }

            console.error(
                "Failed to ask repository question:",
                requestError
            );

            setError(
                requestError.message ||
                "Failed to generate an answer."
            );
        } finally {
            if (requestId === requestIdRef.current) {
                setIsAsking(false);
            }
        }
    }

    // Submit a question to the backend.
    async function handleSubmit(event) {
        event.preventDefault();

        const trimmedQuestion = question.trim();

        if (!trimmedQuestion || !repositoryName || isAsking) {
            return;
        }

        updateMessages((previousMessages) => [
            ...previousMessages,
            {
                role: "user",
                content: trimmedQuestion,
            },
        ]);

        setQuestion("");

        await runQuery(trimmedQuestion);
    }

    // Stop waiting for the current answer.
    function handleStop() {
        requestIdRef.current += 1;
        setIsAsking(false);
    }

    // Ask the last question again.
    function handleRegenerate() {
        if (isAsking || !repositoryName) {
            return;
        }

        let lastUserIndex = -1;

        messages.forEach((message, index) => {
            if (message.role === "user") {
                lastUserIndex = index;
            }
        });

        if (lastUserIndex === -1) {
            return;
        }

        const lastQuestion = messages[lastUserIndex].content;

        updateMessages((previousMessages) =>
            previousMessages.slice(0, lastUserIndex + 1)
        );

        runQuery(lastQuestion);
    }

    // Start a fresh conversation.
    function handleNewChat() {
        requestIdRef.current += 1;

        updateMessages(() => []);
        setError(null);
        setIsAsking(false);
        setQuestion("");
    }

    async function handleCopyAnswer(content, index) {
        try {
            await navigator.clipboard.writeText(content);
            setCopiedIndex(index);
            setTimeout(() => setCopiedIndex(null), 1500);
        } catch (copyError) {
            console.error("Failed to copy answer:", copyError);
        }
    }

    function applySuggestion(suggestion) {
        setQuestion(suggestion);
        textareaRef.current?.focus();
    }

    const lastAssistantIndex = messages.reduce(
        (found, message, index) =>
            message.role === "assistant" ? index : found,
        -1
    );

    return (
        <aside
            className={
                fullscreen
                    ? "da-pop fixed inset-0 z-40 flex flex-col bg-[#06070d]/95 backdrop-blur-xl"
                    : "da-glass da-slide-in flex h-full w-[360px] shrink-0 flex-col border-y-0 border-r-0"
            }
        >

            {/* Chat header */}
            <header className="shrink-0 border-b border-white/10 p-4">
                <div className="flex items-center gap-3">
                    <Avatar />

                    <div className="min-w-0 flex-1">
                        <h2 className="da-display text-base font-bold text-white">
                            AI Code Assistant
                        </h2>

                        <p className="truncate text-xs text-gray-500">
                            {repositoryName || "No repository selected"}
                        </p>
                    </div>

                    {messages.length > 0 && (
                        <IconButton label="New chat" onClick={handleNewChat}>
                            <Icon name="plus" />
                        </IconButton>
                    )}

                    <IconButton
                        label={fullscreen ? "Exit full screen" : "Full screen"}
                        onClick={() => setFullscreen((value) => !value)}
                    >
                        <Icon name={fullscreen ? "collapse" : "expand"} />
                    </IconButton>

                    {fullscreen && onClose && (
                        <IconButton
                            label="Close chat"
                            onClick={() => {
                                setFullscreen(false);
                                onClose();
                            }}
                        >
                            <Icon name="close" />
                        </IconButton>
                    )}
                </div>

                {!fullscreen && (
                    <p className="mt-3 text-xs text-gray-400">
                        Ask questions about your repository's code.
                    </p>
                )}
            </header>

            {/* Conversation */}
            <div
                className="flex-1 overflow-y-auto p-4"
                aria-live="polite"
            >
                <div
                    className={
                        fullscreen
                            ? "mx-auto w-full max-w-3xl space-y-7 py-4"
                            : "space-y-4"
                    }
                >
                    {!repositoryName && (
                        <div className="rounded-xl border border-dashed border-white/10 bg-white/[0.02] p-4">
                            <p className="text-sm text-gray-400">
                                Analyze a GitHub repository before asking
                                questions about its code.
                            </p>
                        </div>
                    )}

                    {repositoryName && messages.length === 0 && (
                        <div className="da-rise space-y-3">
                            {fullscreen && (
                                <div className="pb-4 pt-10 text-center">
                                    <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-cyan-400 shadow-xl shadow-violet-500/30">
                                        <Icon name="sparkle" className="h-7 w-7 text-white" />
                                    </div>

                                    <h3 className="da-display text-3xl font-bold text-white">
                                        What would you like to know?
                                    </h3>

                                    <p className="mt-2 text-sm text-gray-400">
                                        Ask anything about{" "}
                                        <span className="text-cyan-300">
                                            {repositoryName}
                                        </span>
                                    </p>
                                </div>
                            )}

                            {!fullscreen && (
                                <p className="text-sm text-gray-400">
                                    Start by asking a question about this
                                    repository.
                                </p>
                            )}

                            <div
                                className={
                                    fullscreen
                                        ? "grid gap-2 sm:grid-cols-2"
                                        : "space-y-2"
                                }
                            >
                                {(fullscreen
                                    ? SUGGESTIONS
                                    : SUGGESTIONS.slice(0, 3)
                                ).map((suggestion) => (
                                    <button
                                        key={suggestion}
                                        type="button"
                                        onClick={() =>
                                            applySuggestion(suggestion)
                                        }
                                        className="da-card block w-full p-3 text-left text-sm text-gray-300"
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {messages.map((message, index) => (
                        <div
                            key={`${index}-${message.role}`}
                            className="da-pop space-y-2"
                        >
                            {message.role === "user" ? (
                                <div
                                    className={`rounded-2xl rounded-br-md bg-gradient-to-br from-violet-600 to-indigo-600 p-3 text-sm text-white shadow-lg shadow-violet-900/30 ${
                                        fullscreen
                                            ? "ml-auto w-fit max-w-[85%]"
                                            : "ml-6"
                                    }`}
                                >
                                    <p
                                        className={`mb-2 text-xs font-semibold text-violet-200 ${
                                            fullscreen ? "hidden" : ""
                                        }`}
                                    >
                                        You
                                    </p>

                                    <div className="whitespace-pre-wrap break-words leading-6">
                                        {message.content}
                                    </div>
                                </div>
                            ) : (
                                <div
                                    className={
                                        fullscreen
                                            ? "flex gap-3"
                                            : "mr-2 rounded-2xl rounded-bl-md border border-white/10 bg-white/[0.04] p-3"
                                    }
                                >
                                    {fullscreen && <Avatar />}

                                    <div className="min-w-0 flex-1 text-sm text-gray-200">
                                        {!fullscreen && (
                                            <p className="mb-2 text-xs font-semibold text-cyan-300">
                                                DEFINE-AI
                                            </p>
                                        )}

                                        <AnswerBody
                                            text={message.content || ""}
                                            animate={Boolean(message.animate)}
                                            onProgress={scrollToBottom}
                                        />

                                        {/* Answer actions */}
                                        <div className="mt-2 flex items-center gap-1">
                                            <IconButton
                                                label="Copy answer"
                                                onClick={() =>
                                                    handleCopyAnswer(
                                                        message.content,
                                                        index
                                                    )
                                                }
                                            >
                                                <Icon
                                                    name={
                                                        copiedIndex === index
                                                            ? "check"
                                                            : "copy"
                                                    }
                                                />
                                            </IconButton>

                                            {index === lastAssistantIndex && (
                                                <IconButton
                                                    label="Regenerate answer"
                                                    onClick={handleRegenerate}
                                                >
                                                    <Icon name="refresh" />
                                                </IconButton>
                                            )}
                                        </div>

                                        {/* Retrieved source files */}
                                        {message.sources?.length > 0 && (
                                            <div className="mt-3 space-y-2">
                                                <p className="text-xs font-semibold text-gray-400">
                                                    Retrieved sources (
                                                    {message.sources.length})
                                                </p>

                                                <div
                                                    className={
                                                        fullscreen
                                                            ? "grid gap-2 sm:grid-cols-2"
                                                            : "space-y-2"
                                                    }
                                                >
                                                    {message.sources.map(
                                                        (source, sourceIndex) => (
                                                            <button
                                                                key={`${source.file_path}-${source.start_line}-${sourceIndex}`}
                                                                type="button"
                                                                onClick={() =>
                                                                    onViewSource(
                                                                        source.file_path,
                                                                        source.start_line,
                                                                        source.end_line
                                                                    )
                                                                }
                                                                className="da-card flex w-full items-start gap-2 p-2.5 text-left"
                                                                title="Open this source in Code View"
                                                            >
                                                                <Icon
                                                                    name="file"
                                                                    className="mt-0.5 h-4 w-4 shrink-0 text-cyan-300"
                                                                />

                                                                <span className="min-w-0">
                                                                    <span className="block break-all text-xs text-cyan-300">
                                                                        {source.file_path}
                                                                    </span>

                                                                    <span className="mt-1 block text-xs text-gray-500">
                                                                        Lines{" "}
                                                                        {source.start_line}
                                                                        {"–"}
                                                                        {source.end_line}
                                                                    </span>
                                                                </span>
                                                            </button>
                                                        )
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}

                    {isAsking && (
                        <div
                            role="status"
                            className="da-pop flex items-center gap-3 text-sm text-gray-400"
                        >
                            {fullscreen && <Avatar />}

                            <span
                                className={`flex items-center gap-3 ${
                                    fullscreen
                                        ? ""
                                        : "rounded-2xl rounded-bl-md border border-white/10 bg-white/[0.04] p-3"
                                }`}
                            >
                                <span className="flex items-center gap-1" aria-hidden="true">
                                    <span className="da-dot" />
                                    <span className="da-dot" style={{ animationDelay: "0.15s" }} />
                                    <span className="da-dot" style={{ animationDelay: "0.3s" }} />
                                </span>
                                Searching the code and generating an answer...
                            </span>
                        </div>
                    )}

                    {error && (
                        <div
                            role="alert"
                            className="da-pop rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300"
                        >
                            {error}
                        </div>
                    )}

                    <div ref={bottomRef} />
                </div>
            </div>

            {/* Question input */}
            <form
                onSubmit={handleSubmit}
                className={`shrink-0 p-3 ${
                    fullscreen ? "px-4 pb-5" : "border-t border-white/10"
                }`}
            >
                <div className={fullscreen ? "mx-auto w-full max-w-3xl" : ""}>
                    <textarea
                        ref={textareaRef}
                        value={question}
                        onChange={(event) =>
                            setQuestion(event.target.value)
                        }
                        onKeyDown={(event) => {
                            if (
                                event.key === "Enter" &&
                                !event.shiftKey &&
                                !event.nativeEvent.isComposing
                            ) {
                                event.preventDefault();

                                if (!isAsking) {
                                    handleSubmit(event);
                                }
                            }
                        }}
                        placeholder={
                            repositoryName
                                ? "Ask about this repository..."
                                : "Analyze a repository first..."
                        }
                        aria-label="Ask a question about the repository"
                        disabled={!repositoryName || isAsking}
                        rows={fullscreen ? 2 : 3}
                        maxLength={2000}
                        className={`da-input w-full resize-none rounded-xl p-3 text-white outline-none placeholder:text-gray-500 disabled:cursor-not-allowed disabled:opacity-50 ${
                            fullscreen ? "text-base" : "text-sm"
                        }`}
                    />

                    <div className="mt-2 flex items-center justify-between gap-2">
                        <span className="text-xs text-gray-500">
                            Enter to send · Shift+Enter for a new line
                            {question.length > 1500 &&
                                ` · ${question.length}/2000`}
                        </span>

                        {isAsking ? (
                            <button
                                type="button"
                                onClick={handleStop}
                                className="da-btn-ghost flex shrink-0 items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white"
                            >
                                <Icon name="stop" className="h-3.5 w-3.5" />
                                Stop
                            </button>
                        ) : (
                            <button
                                type="submit"
                                disabled={
                                    !repositoryName ||
                                    !question.trim()
                                }
                                className="da-btn-primary flex shrink-0 items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                Ask
                                <Icon name="send" className="h-3.5 w-3.5" />
                            </button>
                        )}
                    </div>
                </div>
            </form>
        </aside>
    );
}

export default RepositoryChat;