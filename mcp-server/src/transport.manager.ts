import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { randomUUID } from "node:crypto";

const transports = {
  streamable: {} as Record<string, StreamableHTTPServerTransport>,
};

export function getTransport(
  sessionId: string | undefined,
  type: "streamable" = "streamable"
): StreamableHTTPServerTransport | undefined {
  return sessionId ? transports[type][sessionId] : undefined;
}

export function setTransport(
  sessionId: string,
  transport: StreamableHTTPServerTransport,
  type: "streamable" = "streamable"
) {
  transports.streamable[sessionId] = transport;
}

export function deleteTransport(
  sessionId: string,
  type: "streamable" = "streamable"
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
