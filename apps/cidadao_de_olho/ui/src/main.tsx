/**
 * Bootstrap do frontend React.
 *
 * Este arquivo inicializa a aplicação e aplica a folha de estilos global.
 */
import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "./App";
import "./styles.css";

/** Monta a aplicação no elemento raiz entregue pelo `index.html`. */
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
