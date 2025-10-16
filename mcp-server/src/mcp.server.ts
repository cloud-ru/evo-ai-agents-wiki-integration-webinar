import { z } from "zod";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { outlineSearchService } from "./outline-search.service.js";
import { SEARCH_OFFSET, SEARCH_LIMIT } from "./config.js";

export function createMcpServer() {
  const mcp = new McpServer({ name: "search-server", version: "1.0.0" });

  mcp.registerTool(
    "search",
    {
      title: "Search",
      description:
        "Search for content using search string. Use it to find information in your wiki through elasticsearch search string. Example query: 'free tier'. Use a comma to search for multiple terms. Example query: 'free tier, AI'",
      inputSchema: {
        query: z.string().min(1, "Search query cannot be empty"),
      },
    },
    async ({ query }) => {
      // Search tool called

      try {
        const results = await outlineSearchService.search({
          query,
          limit: SEARCH_LIMIT,
          offset: SEARCH_OFFSET,
        });

        if (results.length === 0) {
          return {
            content: [
              {
                type: "text",
                text: `No results found for query: "${query}"`,
              },
            ],
          };
        }

        const formattedResults = results
          .map((result, index) => {
            const title = result.document.title;
            const url = result.document.url;
            const text = result.document.text;

            return `${index + 1}. **${title}**\n   URL: ${url}\n   Text: ${text}`;
          })
          .join("\n\n");

        return {
          content: [
            {
              type: "text",
              text: `Found ${results.length} results for "${query}":\n\n${formattedResults}`,
            },
          ],
        };
      } catch (error) {
        // Search error occurred
        return {
          content: [
            {
              type: "text",
              text: `Search failed: ${error instanceof Error ? error.message : "Unknown error"}`,
            },
          ],
        };
      }
    }
  );

  return mcp;
}
