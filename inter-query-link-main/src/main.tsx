import React from "react"; // Adicione este import
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {" "}
    {/* Adicionado para boas práticas */}
    <App />
  </React.StrictMode>
);
