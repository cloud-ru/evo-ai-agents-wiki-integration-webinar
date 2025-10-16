import axios, { AxiosInstance } from "axios";
// @ts-ignore - tunnel package doesn't have TypeScript definitions
import tunnel from "tunnel";
import { OUTLINE_BASE_URL, OUTLINE_TOKEN } from "./config.js";

export interface OutlineSearchRequest {
  /** The search term the user typed. */
  query: string;
  /** Max results (default 20, Outline hard-limit 100). */
  limit?: number;
  /** Pagination cursor returned by previous call. */
  offset?: number;
}

export interface OutlineSearchResult {
  ranking: number;
  context: string;
  document: {
    id: string;
    title: string;
    url: string;
    collectionId: string;
    text: string;
    createdAt: string;
    updatedAt: string;
    createdBy: {
      name: string;
    };
  };
}

export interface OutlineSearchResponse {
  data: OutlineSearchResult[];
  pagination: {
    limit: number;
    offset: number;
    nextPath?: string;
    total: number;
  };
  policies: unknown[];
  status: number;
  ok: boolean;
}

export interface IHttpClient {
  post<T>(url: string, data: unknown): Promise<{ data: T }>;
}

export class AxiosHttpClient implements IHttpClient {
  private client: AxiosInstance;

  constructor(baseURL: string, token: string, timeout: number = 30_000) {
    // Read the proxy URL from either uppercase or lowercase env vars
    const proxyUrlString =
      process.env.HTTPS_PROXY ||
      process.env.https_proxy ||
      process.env.HTTP_PROXY ||
      process.env.http_proxy;

    // Build common axios config
    const axiosConfig: any = {
      baseURL,
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      timeout,
    };

    // If a proxy is configured, create a tunnel agent
    if (proxyUrlString) {
      axiosConfig.proxy = false;
      const proxyUrl = new URL(proxyUrlString);
      axiosConfig.httpsAgent = tunnel.httpsOverHttp({
        proxy: {
          host: proxyUrl.hostname,
          port: Number(proxyUrl.port) || 80,
          proxyAuth:
            proxyUrl.username && proxyUrl.password
              ? `${proxyUrl.username}:${proxyUrl.password}`
              : undefined,
        },
      });
    }

    this.client = axios.create(axiosConfig);
  }

  async post<T>(url: string, data: unknown): Promise<{ data: T }> {
    return await this.client.post<T>(url, data);
  }
}

export interface ISearchService {
  search(params: OutlineSearchRequest): Promise<OutlineSearchResult[]>;
}

export class OutlineSearchService implements ISearchService {
  private httpClient: IHttpClient;

  constructor(httpClient: IHttpClient) {
    this.httpClient = httpClient;
  }

  async search(params: OutlineSearchRequest): Promise<OutlineSearchResult[]> {
    try {
      const response = await this.httpClient.post<OutlineSearchResponse>(
        "/documents.search",
        params,
      );

      // Check if the response structure is as expected
      if (!response.data || !Array.isArray(response.data.data)) {
        // Unexpected response structure
        throw new Error("Invalid response structure from Outline API");
      }

      return response.data.data;
    } catch (error) {
      this.handleSearchError(error);
      throw error;
    }
  }

  private handleSearchError(_error: unknown): void {
    // Outline search failed
    // Response data available if needed for debugging
  }
}

export class SearchServiceFactory {
  static createOutlineSearchService(): ISearchService {
    if (!OUTLINE_BASE_URL || !OUTLINE_TOKEN) {
      throw new Error(
        "OUTLINE_BASE_URL and OUTLINE_TOKEN must be configured in environment variables",
      );
    }

    const httpClient = new AxiosHttpClient(OUTLINE_BASE_URL, OUTLINE_TOKEN);

    return new OutlineSearchService(httpClient);
  }
}

export const outlineSearchService =
  SearchServiceFactory.createOutlineSearchService();
