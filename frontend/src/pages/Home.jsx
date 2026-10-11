import { useState } from "react";

import {
  analyzeRepository,
  getRepositoryFile,
} from "../api";

import CodeView from "../components/CodeView";
import RepositoryGraph from "../components/RepositoryGraph";
import NodeDetails from "../components/NodeDetails";
import RepositoryChat from "../components/RepositoryChat";
import ConstellationHero from "../components/ConstellationHero";

import "../theme.css";

function Home() {
  // -----------------------------------------------
  // Repository state
  // -----------------------------------------------

  const [githubUrl, setGithubUrl] = useState("");
  const [graph, setGraph] = useState(null);
  const [repositoryName, setRepositoryName] = useState(null);
  const [showChat, setShowChat] = useState(false);

  const [analyzingRepository, setAnalyzingRepository] =
    useState(false);

  const [analysisError, setAnalysisError] = useState(null);

  // -----------------------------------------------
  // Selected graph node
  // -----------------------------------------------

  const [selectedNode, setSelectedNode] = useState(null);

  // -----------------------------------------------
  // Code viewer state
  // -----------------------------------------------

  const [selectedFile, setSelectedFile] = useState(null);
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState(null);

  const [selectedRange, setSelectedRange] = useState({
    start: null,
    end: null,
  });

  // -----------------------------------------------
  // Analyze GitHub repository
  // -----------------------------------------------

  async function handleAnalyzeRepository() {
    const url = githubUrl.trim();

    if (!url) {
      setAnalysisError(
        "Please enter a GitHub repository URL."
      );
      return;
    }

    try {
      setAnalyzingRepository(true);
      setAnalysisError(null);

      // Clear previous repository data
      setGraph(null);
      setRepositoryName(null);
      setSelectedNode(null);
      setSelectedFile(null);
      setFileError(null);

      setSelectedRange({
        start: null,
        end: null,
      });

      // Send URL to FastAPI backend
      const data = await analyzeRepository(url);

      // Save returned repository data
      setRepositoryName(data.repository);
      setGraph(data.graph);
    } catch (error) {
      console.error("Repository analysis failed:", error);

      setAnalysisError(
        error.message || "Failed to analyze repository."
      );
    } finally {
      setAnalyzingRepository(false);
    }
  }

  // -----------------------------------------------
  // Open file from graph node details
  // -----------------------------------------------

  async function openFile(
    filePath,
    lineStart = null,
    lineEnd = null
  ) {
    if (!repositoryName) {
      setFileError("Please analyze a repository first.");
      return;
    }

    try {
      setFileLoading(true);
      setFileError(null);
      setSelectedFile(null);

      setSelectedRange({
        start: lineStart,
        end: lineEnd,
      });

      const data = await getRepositoryFile(
        repositoryName,
        filePath
      );

      setSelectedFile(data);
    } catch (error) {
      console.error("Failed to open repository file:", error);

      setFileError(
        error.message || "Failed to load file."
      );
    } finally {
      setFileLoading(false);
    }
  }

  // -----------------------------------------------
  // Render page
  // -----------------------------------------------

  return (
    <div className="relative h-screen flex flex-col overflow-hidden text-white">
      {/* Ambient background */}
      <div className="da-bg" aria-hidden="true">
        <div
          className="da-orb"
          style={{
            width: 420,
            height: 420,
            top: "-12%",
            right: "8%",
            background: "#7c3aed",
          }}
        />
        <div
          className="da-orb"
          style={{
            width: 360,
            height: 360,
            bottom: "-14%",
            left: "6%",
            background: "#0891b2",
            animationDelay: "-8s",
          }}
        />
      </div>

      {/* Header */}
      <header className="da-glass relative z-10 h-[70px] shrink-0 border-x-0 border-t-0 flex items-center px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-cyan-400 shadow-lg shadow-violet-500/30">
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
              <circle cx="12" cy="5" r="2" />
              <circle cx="5" cy="19" r="2" />
              <circle cx="19" cy="19" r="2" />
              <path d="M12 7v4M12 11l-6 6M12 11l6 6" />
            </svg>
          </div>

          <div>
            <h1 className="da-display text-xl font-extrabold leading-none">
              define-ai
            </h1>

            <p className="mt-1 text-xs text-gray-400">
              Repository Intelligence System
            </p>
          </div>
        </div>

        <div className="ml-auto flex items-center gap-4">
          <span
            className="flex max-w-[240px] items-center gap-2 truncate rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-gray-300"
            title={repositoryName || ""}
          >
            <span
              className={`h-2 w-2 shrink-0 rounded-full ${
                repositoryName
                  ? "bg-emerald-400 shadow-[0_0_10px_#34d399]"
                  : "bg-gray-600"
              }`}
            />
            <span className="truncate">
              {repositoryName || "No repository selected"}
            </span>
          </span>

          <button
            type="button"
            onClick={() => setShowChat((visible) => !visible)}
            aria-expanded={showChat}
            className={`da-btn-ghost flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white ${
              showChat ? "!border-violet-500/70 !bg-violet-500/15" : ""
            }`}
          >
            <svg
              viewBox="0 0 24 24"
              className="h-4 w-4 text-cyan-300"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z" />
              <path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z" />
            </svg>
            {showChat ? "Close AI Chat" : "Ask AI"}
          </button>
        </div>
      </header>

      {/* Dynamic GitHub URL input */}
      <form
        className="relative z-10 shrink-0 px-6 py-4 flex gap-3 items-center"
        onSubmit={(event) => {
          event.preventDefault();

          if (!analyzingRepository) {
            handleAnalyzeRepository();
          }
        }}
      >
        <div className="relative flex-1 min-w-0">
          <svg
            viewBox="0 0 24 24"
            className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M10 13a5 5 0 007.5.5l3-3a5 5 0 00-7-7l-1.7 1.7" />
            <path d="M14 11a5 5 0 00-7.5-.5l-3 3a5 5 0 007 7l1.7-1.7" />
          </svg>

          <input
            type="url"
            value={githubUrl}
            onChange={(event) =>
              setGithubUrl(event.target.value)
            }
            placeholder="https://github.com/user/repository"
            aria-label="GitHub repository URL"
            disabled={analyzingRepository}
            className="da-input w-full min-w-0 rounded-xl py-2.5 pl-10 pr-3 text-white outline-none placeholder:text-gray-500 disabled:opacity-60"
          />
        </div>

        <button
          type="submit"
          disabled={analyzingRepository}
          className="da-btn-primary flex items-center gap-2 rounded-xl px-5 py-2.5 font-medium disabled:cursor-not-allowed disabled:opacity-60"
        >
          {analyzingRepository && <span className="da-spinner" />}
          {analyzingRepository
            ? "Analyzing..."
            : "Analyze Repository"}
        </button>
      </form>

      {/* Analysis error */}
      {analysisError && (
        <div
          role="alert"
          className="da-pop relative z-10 mx-6 mb-3 shrink-0 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-sm text-red-300"
        >
          {analysisError}
        </div>
      )}

      {/* Main workspace */}
      <div className="relative z-10 flex flex-1 min-h-0">
        <main className="flex-1 min-w-0">
          {graph ? (
            <RepositoryGraph
              graph={graph}
              onNodeSelect={setSelectedNode}
            />
          ) : (
            <div className="h-full flex items-center justify-center px-6 text-center">
              <div className="da-rise max-w-xl">
                <ConstellationHero analyzing={analyzingRepository} />

                <h2 className="da-display mt-6 text-3xl font-bold text-white sm:text-4xl">
                  {analyzingRepository
                    ? "Mapping your repository"
                    : "See how any codebase fits together"}
                </h2>

                <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-gray-400">
                  {analyzingRepository
                    ? "Analyzing repository and building graph..."
                    : "Paste a GitHub repository URL above and select Analyze Repository to explore its folders, files, classes and imports as an interactive graph."}
                </p>

                {analyzingRepository && (
                  <div className="mx-auto mt-6 h-1.5 w-56 overflow-hidden rounded-full bg-white/5">
                    <div className="da-skeleton h-full w-full" />
                  </div>
                )}
              </div>
            </div>
          )}
        </main>

        {/* AI repository chat */}
        {showChat && (
          <RepositoryChat
            repositoryName={repositoryName}
            onViewSource={openFile}
            onClose={() => setShowChat(false)}
          />
        )}

        {/* Selected node details */}
        <NodeDetails
          node={selectedNode}
          repositoryName={repositoryName}
          onClose={() => setSelectedNode(null)}
          onViewCode={openFile}
        />

        {/* Code viewer */}
        {selectedFile || fileLoading || fileError ? (
          <CodeView
            file={selectedFile}
            loading={fileLoading}
            error={fileError}
            lineStart={selectedRange.start}
            lineEnd={selectedRange.end}
            onClose={() => {
              setSelectedFile(null);
              setFileError(null);

              setSelectedRange({
                start: null,
                end: null,
              });
            }}
          />
        ) : null}
      </div>
    </div>
  );
}

export default Home;