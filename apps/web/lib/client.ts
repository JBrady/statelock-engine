import type { ProxyHeaders, ProxyPayload } from "@/lib/types";

export class HttpError extends Error {
  status: number;
  data: unknown;
  headers: ProxyHeaders;

  constructor(message: string, status: number, data: unknown, headers: ProxyHeaders) {
    super(message);
    this.name = "HttpError";
    this.status = status;
    this.data = data;
    this.headers = headers;
  }
}

function collectHeaders(response: Response): ProxyHeaders {
  return {
    "content-type": response.headers.get("content-type"),
    "content-disposition": response.headers.get("content-disposition"),
    "content-length": response.headers.get("content-length"),
    "cache-control": response.headers.get("cache-control"),
    "x-trace-id": response.headers.get("x-trace-id"),
    "x-statelock-version": response.headers.get("x-statelock-version"),
    "x-statelock-version-requested": response.headers.get("x-statelock-version-requested"),
  };
}

async function parsePayload(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

export async function requestPayload<T>(
  input: string,
  init?: RequestInit,
): Promise<ProxyPayload<T>> {
  const response = await fetch(input, {
    ...init,
    cache: "no-store",
  });
  const headers = collectHeaders(response);
  const data = (await parsePayload(response)) as T;
  if (!response.ok) {
    throw new HttpError(
      typeof data === "string" ? data : `Request failed: ${response.status}`,
      response.status,
      data,
      headers,
    );
  }

  return {
    ok: response.ok,
    status: response.status,
    headers,
    data,
  };
}
