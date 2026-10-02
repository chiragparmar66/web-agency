import { ApiResponse } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface RequestOptions extends RequestInit {
  token?: string;
  params?: Record<string, string | number | boolean | undefined>;
}

export class ApiError extends Error {
  code: string;
  status: number;
  details?: any;

  constructor(message: string, code = "API_ERROR", status = 500, details?: any) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
  const { token, params, headers, ...restOptions } = options;

  let url = `${BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null) {
        searchParams.append(key, String(val));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes("?") ? "&" : "?") + queryString;
    }
  }

  const authHeader: Record<string, string> = {};
  if (typeof window !== "undefined") {
    const storedToken = token || localStorage.getItem("nexus_access_token");
    if (storedToken) {
      authHeader["Authorization"] = `Bearer ${storedToken}`;
    }
  } else if (token) {
    authHeader["Authorization"] = `Bearer ${token}`;
  }

  const requestHeaders: HeadersInit = {
    "Content-Type": "application/json",
    ...authHeader,
    ...headers,
  };

  try {
    const response = await fetch(url, {
      ...restOptions,
      headers: requestHeaders,
    });

    const data = await response.json().catch(() => ({
      success: false,
      message: "Invalid response from server",
    }));

    if (!response.ok) {
      throw new ApiError(
        data.message || `Request failed with status ${response.status}`,
        data.code || "HTTP_ERROR",
        response.status,
        data.details
      );
    }

    return data as ApiResponse<T>;
  } catch (error: any) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(error.message || "Network request failed", "NETWORK_ERROR", 0);
  }
}

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "GET" }),

  post: <T>(endpoint: string, body?: any, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(endpoint: string, body?: any, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(endpoint: string, body?: any, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "DELETE" }),

  upload: async <T>(endpoint: string, formData: FormData, options: RequestOptions = {}): Promise<ApiResponse<T>> => {
    const { token, headers, ...restOptions } = options;
    const url = `${BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

    const authHeader: Record<string, string> = {};
    if (typeof window !== "undefined") {
      const storedToken = token || localStorage.getItem("nexus_access_token");
      if (storedToken) {
        authHeader["Authorization"] = `Bearer ${storedToken}`;
      }
    } else if (token) {
      authHeader["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...restOptions,
        method: "POST",
        body: formData,
        headers: {
          ...authHeader,
          ...headers,
        },
      });

      const data = await response.json().catch(() => ({
        success: false,
        message: "Invalid response from server",
      }));

      if (!response.ok) {
        throw new ApiError(
          data.message || `Upload failed with status ${response.status}`,
          data.code || "HTTP_ERROR",
          response.status,
          data.details
        );
      }

      return data as ApiResponse<T>;
    } catch (error: any) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(error.message || "File upload failed", "NETWORK_ERROR", 0);
    }
  },

  downloadBlob: async (endpoint: string, fallbackFilename?: string): Promise<void> => {
    const url = `${BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
    const authHeader: Record<string, string> = {};
    if (typeof window !== "undefined") {
      const storedToken = localStorage.getItem("nexus_access_token");
      if (storedToken) {
        authHeader["Authorization"] = `Bearer ${storedToken}`;
      }
    }

    const response = await fetch(url, {
      method: "GET",
      headers: authHeader,
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new ApiError(
        errData.message || `Download failed with status ${response.status}`,
        "DOWNLOAD_ERROR",
        response.status
      );
    }

    const disposition = response.headers.get("Content-Disposition");
    let filename = fallbackFilename || "downloaded_file";
    if (disposition) {
      const matchUtf8 = disposition.match(/filename\*=UTF-8''([^;]+)/i);
      if (matchUtf8 && matchUtf8[1]) {
        filename = decodeURIComponent(matchUtf8[1]);
      } else {
        const matchRegular = disposition.match(/filename="?([^";]+)"?/i);
        if (matchRegular && matchRegular[1]) {
          filename = matchRegular[1];
        }
      }
    }

    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(blobUrl);
  },
};
