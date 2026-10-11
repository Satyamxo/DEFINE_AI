
import { useEffect, useMemo, useRef, useState } from "react";


const KEYWORDS = new Set([
  "import", "from", "export", "default", "as", "const", "let", "var",
  "function", "return", "if", "else", "elif", "for", "while", "do",
  "switch", "case", "break", "continue", "try", "catch", "except",
  "finally", "throw", "raise", "new", "class", "extends", "implements",
  "interface", "type", "enum", "struct", "def", "lambda", "async",
  "await", "yield", "with", "pass", "in", "is", "not", "and", "or",
  "of", "typeof", "instanceof", "static", "public", "private",
  "protected", "package", "func", "fn", "pub", "use", "mod", "impl",
  "self", "this", "super", "global", "del", "assert", "void",
]);

const LITERALS = new Set([
  "true", "false", "null", "undefined", "None", "True", "False", "nil",
]);

const HASH_COMMENT_EXTENSIONS = new Set([
  "py", "sh", "bash", "zsh", "rb", "yml", "yaml", "toml", "r", "pl",
  "env", "ini", "cfg", "dockerfile",
]);

function getExtension(path) {
  if (!path) return "";

  const name = path.split("/").pop() || "";
  const dot = name.lastIndexOf(".");

  return dot === -1 ? name.toLowerCase() : name.slice(dot + 1).toLowerCase();
}

function buildTokenRegex(useHashComments) {
  const comment = useHashComments ? "#.*" : "\\/\\/.*|\\/\\*.*?\\*\\/";

  return new RegExp(
    `(${comment})|` +
      `("(?:\\\\.|[^"\\\\])*"|'(?:\\\\.|[^'\\\\])*'|\`(?:\\\\.|[^\`\\\\])*\`)|` +
      `\\b(\\d+(?:\\.\\d+)?)\\b|` +
      `\\b([A-Za-z_$][\\w$]*)\\b`,
    "g"
  );
}

function highlightLine(line, regex) {
  const parts = [];
  let lastIndex = 0;
  let match;

  regex.lastIndex = 0;

  while ((match = regex.exec(line)) !== null) {
    if (match.index > lastIndex) {
      parts.push(line.slice(lastIndex, match.index));
    }

    const [text, comment, string, number, word] = match;
    const key = `${match.index}-${text.length}`;
    const end = match.index + text.length;

    let className = null;

    if (comment) {
      className = "text-gray-500 italic";
    } else if (string) {
      className = "text-emerald-300";
    } else if (number) {
      className = "text-amber-300";
    } else if (word) {
      if (KEYWORDS.has(word)) {
        className = "text-violet-400";
      } else if (LITERALS.has(word)) {
        className = "text-amber-300";
      } else if (line[end] === "(") {
        className = "text-cyan-300";
      } else if (/^[A-Z][a-zA-Z0-9]*$/.test(word)) {
        className = "text-yellow-200";
      }
    }

    parts.push(
      className ? (
        <span key={key} className={className}>
          {text}
        </span>
      ) : (
        text
      )
    );

    lastIndex = end;

    // Guard against zero-length matches.
    if (text.length === 0) {
      regex.lastIndex++;
    }
  }

  if (lastIndex < line.length) {
    parts.push(line.slice(lastIndex));
  }

  return parts;
}

function CodeView({ file, loading, error, onClose, lineStart, lineEnd }) {
  const [copied, setCopied] = useState(false);

  // First highlighted line, used to scroll it into view.
  const highlightRef = useRef(null);

  const lines = useMemo(
    () => (file?.content ? file.content.split("\n") : []),
    [file]
  );

  const extension = getExtension(file?.path);

  const tokenRegex = useMemo(
    () => buildTokenRegex(HASH_COMMENT_EXTENSIONS.has(extension)),
    [extension]
  );

  const hasRange = lineStart !== null && lineEnd !== null;

  // Scroll to the highlighted range when a file opens.
  useEffect(() => {
    if (file && !loading && highlightRef.current) {
      highlightRef.current.scrollIntoView({
        block: "center",
        behavior: "smooth",
      });
    }
  }, [file, loading, lineStart, lineEnd]);

  // Close with the Escape key.
  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // Reset the "Copied" label whenever another file opens.
  useEffect(() => {
    setCopied(false);
  }, [file]);

  async function handleCopy() {
    if (!file?.content) return;

    try {
      await navigator.clipboard.writeText(file.content);
      setCopied(true);

      setTimeout(() => setCopied(false), 1800);
    } catch (copyError) {
      console.error("Failed to copy source code:", copyError);
    }
  }

  // Errors must still render, otherwise a failed load shows nothing.
  if (!file && !loading && !error) {
    return null;
  }

  const pathParts = (file?.path || "").split("/");
  const fileName = pathParts.pop();
  const folderPath = pathParts.join("/");

  return (
    <div className="da-pop fixed inset-0 z-50 flex flex-col bg-[#06070d]/95 text-white backdrop-blur-xl">
      {/* Header */}

      <header className="da-glass flex h-16 shrink-0 items-center gap-4 border-x-0 border-t-0 px-5">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-cyan-400 shadow-lg shadow-violet-500/30">
          <svg
            viewBox="0 0 24 24"
            className="h-5 w-5 text-white"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M8 6l-6 6 6 6" />
            <path d="M16 6l6 6-6 6" />
          </svg>
        </div>

        <div className="min-w-0 flex-1">
          <h2 className="truncate text-sm">
            {file ? (
              <>
                {folderPath && (
                  <span className="text-gray-500">{folderPath}/</span>
                )}
                <span className="da-display text-base font-bold text-white">
                  {fileName}
                </span>
              </>
            ) : (
              <span className="font-semibold text-gray-300">
                Loading...
              </span>
            )}
          </h2>

          <div className="mt-1 flex flex-wrap items-center gap-2">
            {file && (
              <p className="text-xs text-gray-500">
                {file.line_count} lines
              </p>
            )}

            {extension && file && (
              <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[11px] text-gray-400">
                {extension}
              </span>
            )}

            {hasRange && file && (
              <span className="rounded-full border border-yellow-500/40 bg-yellow-500/10 px-2 py-0.5 text-[11px] text-yellow-300">
                Lines {lineStart}–{lineEnd}
              </span>
            )}
          </div>
        </div>

        {file && (
          <button
            type="button"
            onClick={handleCopy}
            className="da-btn-ghost flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-gray-300 hover:text-white"
          >
            <svg
              viewBox="0 0 24 24"
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              {copied ? (
                <path d="M5 13l4 4L19 7" />
              ) : (
                <>
                  <rect x="9" y="9" width="11" height="11" rx="2" />
                  <path d="M5 15V6a2 2 0 012-2h9" />
                </>
              )}
            </svg>
            {copied ? "Copied" : "Copy"}
          </button>
        )}

        <button
          onClick={onClose}
          className="da-btn-ghost flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-gray-300 hover:text-white"
          title="Close (Esc)"
        >
          Close
          <kbd className="rounded border border-white/15 bg-white/5 px-1.5 text-[10px] text-gray-500">
            Esc
          </kbd>
        </button>
      </header>

      {/* Content */}

      <div className="flex-1 overflow-auto bg-[#0a0c14]/80">
        {loading && (
          <div className="mx-auto max-w-3xl space-y-3 p-8" role="status">
            <p className="flex items-center gap-3 text-sm text-gray-400">
              <span className="da-spinner" />
              Loading source code...
            </p>

            {[92, 70, 84, 55, 78, 40, 66].map((width, index) => (
              <div
                key={index}
                className="da-skeleton h-4 rounded"
                style={{ width: `${width}%` }}
              />
            ))}
          </div>
        )}

        {error && (
          <div className="mx-auto max-w-xl p-8">
            <div
              role="alert"
              className="da-pop rounded-2xl border border-red-500/30 bg-red-500/10 p-5"
            >
              <h3 className="da-display font-semibold text-red-300">
                Failed to load source code
              </h3>

              <p className="mt-2 text-sm text-gray-400">{error}</p>
            </div>
          </div>
        )}

        {file && !loading && !error && (
          <pre className="w-max min-w-full py-4 font-mono text-sm leading-6">
            {lines.map((line, index) => {
              const lineNumber = index + 1;

              const isHighlighted =
                lineStart !== null &&
                lineEnd !== null &&
                lineNumber >= lineStart &&
                lineNumber <= lineEnd;

              const isFirstHighlighted =
                isHighlighted && lineNumber === lineStart;

              return (
                <div
                  key={index}
                  ref={isFirstHighlighted ? highlightRef : null}
                  className={`flex border-l-2 ${
                    isHighlighted
                      ? "border-yellow-400 bg-yellow-400/10"
                      : "border-transparent hover:bg-white/[0.04]"
                  }`}
                >
                  <span
                    className={`sticky left-0 w-16 shrink-0 select-none pr-4 text-right ${
                      isHighlighted
                        ? "bg-[#17150a] text-yellow-400"
                        : "bg-[#0a0c14] text-gray-600"
                    }`}
                  >
                    {lineNumber}
                  </span>

                  <code
                    className={`whitespace-pre pr-8 ${
                      isHighlighted ? "text-yellow-50" : "text-gray-300"
                    }`}
                  >
                    {highlightLine(line, tokenRegex)}
                  </code>
                </div>
              );
            })}
          </pre>
        )}
      </div>

      {/* Status bar */}

      {file && !loading && !error && (
        <footer className="da-glass flex h-8 shrink-0 items-center gap-4 border-x-0 border-b-0 px-5 text-xs text-gray-500">
          <span className="truncate">{file.path}</span>
          <span className="ml-auto shrink-0">{lines.length} lines</span>
        </footer>
      )}
    </div>
  );
}

export default CodeView;