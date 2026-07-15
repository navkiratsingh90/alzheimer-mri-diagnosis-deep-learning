import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
//process.env.NEXT_PUBLIC_BACKEND_URL 

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // send cookies (JWT stored in HTTP-only cookie)
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor for handling authentication errors
// api.interceptors.response.use(
//   (response) => response,
//   (error) => {
//     if (error.response?.status === 401) {
//       if (typeof window !== "undefined") {
//         window.location.href = "/login";
//       }
//     }
//     return Promise.reject(error);
//   }
// );

export default api;