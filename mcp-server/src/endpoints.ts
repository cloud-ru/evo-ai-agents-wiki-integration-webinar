import express from "express";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import type { Express } from "express";
import {
  getTransport,
  setTransport,
  deleteTransport,
  createTransport,
} from "./transport.manager.js";

export function registerEndpoints(
  app: Express,
  _transports: unknown, // no longer used
  createMcpServer: () => unknown
) {
  app.post("/mcp", async (req, res, next) => {
    try {
      const sessionId = req.headers["mcp-session-id"] as string | undefined;
      let transport = getTransport(
        sessionId,
        "streamable"
      ) as StreamableHTTPServerTransport;

      if (!transport && isInitializeRequest(req.body)) {
        // Creating new session
        transport = createTransport((id) => {
          // Session opened
          if (transport) {
            setTransport(id, transport, "streamable");
          }
        });

        transport.onclose = () => {
          if (transport?.sessionId) {
            // Session closed
            deleteTransport(transport.sessionId, "streamable");
          }
        };

        const server = createMcpServer() as any;
        await server.connect(transport);
      }

      if (!transport) {
        return res.status(400).json({
          jsonrpc: "2.0",
          error: {
            code: -32000,
            message:
              "Bad Request: No valid session ID provided or not an initialization request.",
          },
          id: null,
        });
      }

      await transport.handleRequest(req, res, req.body);
    } catch (err) {
      next(err);
    }
  });

  const handleSessionRequest = async (
    req: express.Request,
    res: express.Response,
    next: express.NextFunction
  ) => {
    try {
      const sessionId = req.headers["mcp-session-id"] as string | undefined;
      const transport = getTransport(
        sessionId,
        "streamable"
      ) as StreamableHTTPServerTransport;

      if (!transport) {
        return res.status(400).send("Invalid or missing session ID");
      }

      await transport.handleRequest(req, res);
    } catch (err) {
      next(err);
    }
  };

  app.get("/mcp", handleSessionRequest);
  app.delete("/mcp", handleSessionRequest);

  app.use(
    (
      err: Error,
      _req: express.Request,
      res: express.Response,
      _next: express.NextFunction
    ) => {
      // Express error handler
      res
        .status(res.statusCode !== 200 ? res.statusCode : 500)
        .json({ error: err.message, stack: err.stack });
    }
  );
}
