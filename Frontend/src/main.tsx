import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles/index.css";
import "./styles/theme.css";

const root = document.getElementById("root");
if (!root) throw new Error('The application requires a <div id="root"> element.');

createRoot(root).render(

    <App />

);
