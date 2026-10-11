
import { Routes, Route, Navigate, useLocation } from "react-router-dom";

import Home from "./pages/Home";
import CodeViewPage from "./pages/CodeViewPage";

function App() {
  const location = useLocation();
  const isCodeView = location.pathname === "/code-view";

  return (
    <>
      {/*
        Home stays mounted at all times so the repository, graph,
        chat history and URL input survive a trip to /code-view.
        It is only hidden while the code page is open.
      */}
      <div className={isCodeView ? "hidden" : "block"}>
        <Home />
      </div>

      <Routes>
        <Route path="/" element={null} />
        <Route path="/code-view" element={<CodeViewPage />} />

        {/* Unknown URLs go back to the home page */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default App;