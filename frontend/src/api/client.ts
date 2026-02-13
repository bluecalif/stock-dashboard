import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    const msg =
      error.response?.data?.detail || error.message || "Unknown error";
    console.error(`[API] ${error.config?.method?.toUpperCase()} ${error.config?.url} → ${msg}`);
    return Promise.reject(error);
  },
);

export default apiClient;
