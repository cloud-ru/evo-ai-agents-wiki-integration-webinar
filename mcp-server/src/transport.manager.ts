import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { randomUUID } from "node:crypto";
import type { ServerResponse } from "node:http";

const transports = {
  streamable: {} as Record<string, StreamableHTTPServerTransport>,
  sse: {} as Record<string, SSEServerTransport>,
};

export function getTransport(
  sessionId: string | undefined,
  type: "streamable" | "sse" = "streamable",
): StreamableHTTPServerTransport | SSEServerTransport | undefined {
  return sessionId ? transports[type][sessionId] : undefined;
}

export function setTransport(
  sessionId: string,
  transport: StreamableHTTPServerTransport | SSEServerTransport,
  type: "streamable" | "sse" = "streamable",
) {
  if (type === "streamable") {
    transports.streamable[sessionId] =
      transport as StreamableHTTPServerTransport;
  } else {
    transports.sse[sessionId] = transport as SSEServerTransport;
  }
}

export function deleteTransport(
  sessionId: string,
  type: "streamable" | "sse" = "streamable",
) {
  delete transports[type][sessionId];
}

export function createTransport(onSessionInitialized: (id: string) => void) {
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: () => randomUUID(),
    onsessioninitialized: onSessionInitialized,
  });
  return transport;
}

export function createSSETransport(path: string, res: ServerResponse) {
  const transport = new SSEServerTransport(path, res);
  return transport;
}
