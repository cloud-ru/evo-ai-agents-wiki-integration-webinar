import express from "express";
import cors from "cors";
import morgan from "morgan";

import { registerEndpoints } from "./endpoints.js";
import { createMcpServer } from "./mcp.server.js";
import { PORT } from "./config.js";

console.log("Starting MCP server...");
console.log("PORT:", PORT);

/* ───────────── HTTP wrapper ───────────── */
const app = express();

app.use(morgan("combined"));
app.use(
  cors({
    origin: "*",
    exposedHeaders: ["Mcp-Session-Id"],
    allowedHeaders: ["Content-Type", "mcp-session-id"],
  }),
);

app.use(express.json());

registerEndpoints(app, undefined, createMcpServer);

app
  .listen(PORT, () => {
    console.log(`MCP server ready on port ${PORT}`);
    console.log("MCP server is running without authentication");
  })
  .on("error", (err) => {
    console.error("Server startup error:", err);
    process.exit(1);
  });
