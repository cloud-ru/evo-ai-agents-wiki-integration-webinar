import express from "express";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import type { Express } from "express";
import {
  getTransport,
  setTransport,
  deleteTransport,
  createTransport,
  createSSETransport,
} from "./transport.manager.js";

export function registerEndpoints(
  app: Express,
  _transports: unknown, // no longer used
  createMcpServer: () => unknown,
) {
  app.post("/", async (req, res, next) => {
    try {
      const sessionId = req.headers["mcp-session-id"] as string | undefined;
      let transport = getTransport(
        sessionId,
        "streamable",
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
    next: express.NextFunction,
  ) => {
    try {
      const sessionId = req.headers["mcp-session-id"] as string | undefined;
      const transport = getTransport(
        sessionId,
        "streamable",
      ) as StreamableHTTPServerTransport;

      if (!transport) {
        return res.status(400).send("Invalid or missing session ID");
      }

      await transport.handleRequest(req, res);
    } catch (err) {
      next(err);
    }
  };

  app.get("/", handleSessionRequest);
  app.delete("/", handleSessionRequest);

  // Legacy SSE endpoint for older clients
  app.get("/sse", async (req, res, next) => {
    try {
      // Set proper SSE headers
      res.setHeader("Content-Type", "text/event-stream");
      res.setHeader("Cache-Control", "no-cache");
      res.setHeader("Connection", "keep-alive");
      res.setHeader("Access-Control-Allow-Origin", "*");
      res.setHeader("Access-Control-Allow-Headers", "Cache-Control");

      // Create SSE transport for legacy clients
      const transport = createSSETransport(
        "/messages",
        res,
      ) as SSEServerTransport;

      // Store the transport with its session ID
      setTransport(transport.sessionId, transport, "sse");

      // Handle connection close
      res.on("close", () => {
        deleteTransport(transport.sessionId, "sse");
      });

      // Connect the MCP server to the transport
      const server = createMcpServer() as any;
      await server.connect(transport);
    } catch (err) {
      next(err);
    }
  });

  // Legacy message endpoint for older clients
  app.post("/messages", async (req, res, next) => {
    try {
      const sessionId = req.query.sessionId as string;

      if (!sessionId) {
        return res.status(400).json({
          jsonrpc: "2.0",
          error: {
            code: -32600,
            message: "Invalid Request: sessionId parameter is required",
          },
          id: null,
        });
      }

      const transport = getTransport(sessionId, "sse") as SSEServerTransport;
      if (transport) {
        await transport.handlePostMessage(req, res, req.body);
      } else {
        res.status(400).json({
          jsonrpc: "2.0",
          error: {
            code: -32600,
            message: `No transport found for sessionId: ${sessionId}`,
          },
          id: null,
        });
      }
    } catch (err) {
      next(err);
    }
  });

  app.use(
    (
      err: Error,
      _req: express.Request,
      res: express.Response,
      _next: express.NextFunction,
    ) => {
      // Express error handler
      res
        .status(res.statusCode !== 200 ? res.statusCode : 500)
        .json({ error: err.message, stack: err.stack });
    },
  );
}
