import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { ShowcaseClient } from "../app/ShowcaseClient";
import "../app/globals.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("GuardianSim showcase root element is missing.");
}

createRoot(root).render(
  <StrictMode>
    <ShowcaseClient />
  </StrictMode>,
);
