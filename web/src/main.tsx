import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { installGlobalTracking } from "./tracker";
import "./styles.css";

installGlobalTracking();
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
