import { useEffect, useState } from "react";
import {
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";

import { getRepositoryFile } from "../api";
import CodeView from "../components/CodeView";

import "../theme.css";

/*
  Standalone route. It accepts its input two ways:

  1) Navigation state (used by the View Code button):
     navigate("/code-view", {
       state: { repositoryName, codeFilePath, lineStart, lineEnd }
     })

  2) URL query params (shareable links):
     /code-view?repo=<repositoryName>&path=<filePath>&start=10&end=40
*/

function toLineNumber(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const number = Number(value);

  return Number.isFinite(number) ? number : null;
}

function CodeViewPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();

  const routeState = location.state || {};

  const repository =
    routeState.repositoryName || searchParams.get("repo");

  const filePath =
    routeState.codeFilePath || searchParams.get("path");

  const lineStart = toLineNumber(
    routeState.lineStart ?? searchParams.get("start")
  );

  const lineEnd = toLineNumber(
    routeState.lineEnd ?? searchParams.get("end")
  );

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadFile() {
      if (!repository || !filePath) {
        setError(
          "Missing repository or file path. Analyze a repository and open the file from the graph."
        );
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        setFile(null);

        const data = await getRepositoryFile(
          repository,
          filePath
        );

        if (!cancelled) {
          setFile(data);
        }
      } catch (requestError) {
        console.error(
          "Failed to open repository file:",
          requestError
        );

        if (!cancelled) {
          setError(
            requestError.message || "Failed to load file."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadFile();

    return () => {
      cancelled = true;
    };
  }, [repository, filePath]);

  return (
    <div className="relative h-screen overflow-hidden">
      <div className="da-bg" aria-hidden="true" />

      <CodeView
        file={file}
        loading={loading}
        error={error}
        lineStart={lineStart}
        lineEnd={lineEnd}
        onClose={() => navigate("/")}
      />
    </div>
  );
}

export default CodeViewPage;