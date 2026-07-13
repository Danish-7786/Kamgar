import axios from "axios";

// Single axios instance for the whole app.
// baseURL comes from .env (VITE_API_BASE_URL) so it can differ per environment.
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});
