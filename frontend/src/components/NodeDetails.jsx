

import { useNavigate } from "react-router-dom";

const TYPE_COLORS = {
  repository: "#7c3aed",
  folder: "#2563eb",
  file: "#059669",
  class: "#d97706",
  function: "#dc2626",
  method: "#db2777",
};

function typeColor(type) {
  return TYPE_COLORS[type] || "#6b7280";
}

function SectionTitle({ children, count }) {
  return (
    <div className="flex items-center justify-between">
      <h3 className="text-sm font-semibold text-gray-300">{children}</h3>

      {count !== undefined && (
        <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-gray-400">
          {count}
        </span>
      )}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>

      <p className="mt-1 text-sm text-gray-200 break-all">{children}</p>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="da-card p-3">
      <p className="text-xs text-gray-500">{label}</p>

      <p className="da-display mt-1 text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

// `onViewCode` is kept in the props so existing callers don't break,
// but View Code now navigates to the /code-view route.
function NodeDetails({ node, onClose, onViewCode, repositoryName }) {
  // Hooks must be called inside the component, before any early return.
  const navigate = useNavigate();

  if (!node) {
    return (
      <aside className="da-glass hidden w-80 shrink-0 border-y-0 border-r-0 p-6 lg:block">
        <div className="h-full flex items-center justify-center">
          <div className="text-center da-rise">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-2xl text-violet-300">
              ◇
            </div>

            <h2 className="da-display text-lg font-semibold text-gray-200">
              No node selected
            </h2>

            <p className="mt-2 text-sm text-gray-500">
              Click a node in the graph to inspect it.
            </p>
          </div>
        </div>
      </aside>
    );
  }

  // React Flow node ke andar API data `data` ke andar
  // ho sakta hai. Direct API node bhi support kar rahe hain.
  const details = node.data || node;

  const isRepository = details.type === "repository";
  const isFolder = details.type === "folder";
  const isFile = details.type === "file";
  const isClass = details.type === "class";
  const isMethod = details.type === "method";
  const isFunction = details.type === "function";

  // Parser analysis bhi data ke andar ya direct node ke andar
  // ho sakta hai.
  const analysis = details.analysis || node.analysis || {};

  const imports = analysis.imports || [];
  const classes = analysis.classes || [];
  const functions = analysis.functions || [];

  /*
   * File nodes use `path`.
   *
   * Class / method / function nodes use `file`.
   *
   * This gives View Code one common file path.
   */
  const codeFilePath = details.path || details.file || null;

  /*
   * Only these node types should be able to open source code.
   */
  const canViewCode = isFile || isClass || isMethod || isFunction;

  const accent = typeColor(details.type);

  return (
    <aside
      // `key` restarts the entrance animation when a new node is picked.
      key={details.id || details.path || details.name}
      className="da-glass da-slide-in w-80 shrink-0 border-y-0 border-r-0 p-6 overflow-y-auto"
    >
      {/* ================= HEADER ================= */}

      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <span
            className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium capitalize text-white"
            style={{
              background: `${accent}33`,
              border: `1px solid ${accent}88`,
            }}
          >
            <span
              className="h-1.5 w-1.5 rounded-full"
              style={{ background: accent }}
            />
            {details.type || "node"}
          </span>

          <h2 className="da-display mt-3 text-xl font-bold text-white break-words">
            {details.name || "Unnamed"}
          </h2>
        </div>

        <button
          onClick={onClose}
          className="ml-3 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-xl text-gray-500 transition hover:bg-white/10 hover:text-white"
          aria-label="Close details"
        >
          ×
        </button>
      </div>

      {/* ================= BASIC INFORMATION ================= */}

      <section className="mt-6">
        <SectionTitle>Basic information</SectionTitle>

        <div className="mt-4 space-y-4">
          {/* Path */}

          {details.path && <Field label="Path">{details.path}</Field>}

          {/* File */}

          {details.file && <Field label="File">{details.file}</Field>}

          {/* Language */}

          {details.language && (
            <Field label="Language">{details.language}</Field>
          )}

          {/* Size */}

          {details.size !== undefined && (
            <Field label="Size">{details.size.toLocaleString()} bytes</Field>
          )}

          {/* Class */}

          {details.class_name && (
            <Field label="Class">{details.class_name}</Field>
          )}

          {/* Lines */}

          {details.line_start !== undefined && (
            <Field label="Lines">
              {details.line_start}
              {" - "}
              {details.line_end}
            </Field>
          )}
        </div>
      </section>

      {/* ================= REPOSITORY / FOLDER STATISTICS ================= */}

      {(isRepository || isFolder) && (
        <section className="mt-8">
          <SectionTitle>Statistics</SectionTitle>

          <div className="mt-4 grid grid-cols-2 gap-3">
            {details.files !== undefined && (
              <StatCard label="Files" value={details.files} />
            )}

            {details.folders !== undefined && (
              <StatCard label="Folders" value={details.folders} />
            )}

            {details.subfolders !== undefined && (
              <StatCard label="Subfolders" value={details.subfolders} />
            )}

            {details.classes !== undefined && (
              <StatCard label="Classes" value={details.classes} />
            )}

            {details.methods !== undefined && (
              <StatCard label="Methods" value={details.methods} />
            )}

            {details.functions !== undefined && (
              <StatCard label="Functions" value={details.functions} />
            )}
          </div>
        </section>
      )}

      {/* ================= IMPORTS ================= */}

      {imports.length > 0 && (
        <section className="mt-8">
          <SectionTitle count={imports.length}>Imports</SectionTitle>

          <div className="mt-3 space-y-2">
            {imports.map((item, index) => (
              <div key={index} className="da-card p-3">
                <p className="text-sm text-gray-200 break-all">
                  {item.module || item.name || "Unknown import"}
                </p>

                {item.name && item.module && (
                  <p className="mt-1 text-xs text-gray-500 break-all">
                    {item.name}

                    {item.alias && (
                      <>
                        {" → "}
                        {item.alias}
                      </>
                    )}
                  </p>
                )}

                {item.line !== undefined && (
                  <p className="mt-1 text-xs text-gray-600">Line {item.line}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ================= CLASSES ================= */}

      {classes.length > 0 && (
        <section className="mt-8">
          <SectionTitle count={classes.length}>Classes</SectionTitle>

          <div className="mt-3 space-y-2">
            {classes.map((item, index) => (
              <div key={index} className="da-card p-3">
                <p className="text-sm font-medium text-amber-200">
                  {item.name || "Unnamed class"}
                </p>

                {(item.line_start !== undefined ||
                  item.line_end !== undefined) && (
                  <p className="mt-1 text-xs text-gray-600">
                    Lines {item.line_start ?? "?"}
                    {" - "}
                    {item.line_end ?? "?"}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ================= FUNCTIONS ================= */}

      {functions.length > 0 && (
        <section className="mt-8">
          <SectionTitle count={functions.length}>Functions</SectionTitle>

          <div className="mt-3 space-y-2">
            {functions.map((item, index) => (
              <div key={index} className="da-card p-3">
                <p className="text-sm font-medium text-rose-200 break-all">
                  {item.name || "Unnamed function"}
                </p>

                {(item.line_start !== undefined ||
                  item.line_end !== undefined) && (
                  <p className="mt-1 text-xs text-gray-600">
                    Lines {item.line_start ?? "?"}
                    {" - "}
                    {item.line_end ?? "?"}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ================= VIEW CODE ================= */}

      {canViewCode && codeFilePath && (
        <button
          onClick={() =>
            navigate("/code-view", {
              state: {
                repositoryName,
                codeFilePath,
                lineStart: details.line_start ?? null,
                lineEnd: details.line_end ?? null,
              },
            })
          }
          className="da-btn-primary w-full mt-6 px-4 py-2.5 rounded-xl font-medium"
        >
          View Code
        </button>
      )}

      {/* ================= NO ANALYSIS ================= */}

      {imports.length === 0 &&
        classes.length === 0 &&
        functions.length === 0 &&
        details.type === "file" && (
          <section className="mt-8">
            <div className="rounded-xl border border-dashed border-white/10 bg-white/[0.02] p-4">
              <p className="text-sm text-gray-500">
                No parsed code structure available for this file.
              </p>
            </div>
          </section>
        )}
    </aside>
  );
}

export default NodeDetails;