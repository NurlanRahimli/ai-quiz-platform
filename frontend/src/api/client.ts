import axios from "axios"

const apiUrl = import.meta.env.VITE_API_URL

if (!apiUrl) {
  throw new Error("VITE_API_URL is not configured")
}

const apiClient = axios.create({
  baseURL: apiUrl,
  headers: {
    "Content-Type": "application/json",
  },
})

export default apiClient