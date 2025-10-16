import dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();

export const PORT = Number(process.env.PORT) || 8080;
export const OUTLINE_BASE_URL = process.env.OUTLINE_BASE_URL || "";
export const OUTLINE_TOKEN = process.env.OUTLINE_TOKEN || "";

// Search configuration
export const SEARCH_OFFSET = 0;
export const SEARCH_LIMIT = Number(process.env.SEARCH_LIMIT) || 2;
