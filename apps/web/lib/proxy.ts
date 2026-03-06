import { type NextRequest, NextResponse } from "next/server";

type ProxyKind = "core" | "obs";

const hopByHopHeaders = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "host",
]);

const requestHeaderAllowlist: Record<ProxyKind, Set<string>> = {
  core: new Set(["content-type", "x-statelock-version"]),
  obs: new Set(["content-type"]),
};

const responseHeaderAllowlist: Record<ProxyKind, Set<string>> = {
  core: new Set([
    "content-type",
    "content-disposition",
    "content-length",
    "cache-control",
    "x-trace-id",
    "x-statelock-version",
    "x-statelock-version-requested",
  ]),
  obs: new Set([
    "content-type",
    "content-disposition",
    "content-length",
    "cache-control",
  ]),
};

function getBaseUrl(kind: ProxyKind): string {
  const baseUrl =
    kind === "core"
      ? process.env.STATELOCK_CORE_BASE_URL
      : process.env.STATELOCK_OBS_BASE_URL;

  if (!baseUrl) {
    throw new Error(
      kind === "core"
        ? "Missing STATELOCK_CORE_BASE_URL"
        : "Missing STATELOCK_OBS_BASE_URL",
    );
  }

  return baseUrl;
}

function buildTargetUrl(kind: ProxyKind, request: NextRequest, path: string[]): URL {
  const baseUrl = new URL(getBaseUrl(kind));
  const safePath = path.map((segment) => encodeURIComponent(segment)).join("/");
  const basePath = baseUrl.pathname.replace(/\/$/, "");
  baseUrl.pathname = `${basePath}/${safePath}`.replace(/\/+/g, "/");
  baseUrl.search = request.nextUrl.search;
  return baseUrl;
}

function getProxyPrefix(kind: ProxyKind): string {
  return kind === "core" ? "/api/core" : "/api/obs";
}

function getSafeRedirectLocation(
  kind: ProxyKind,
  response: Response,
  targetUrl: URL,
): string | null {
  const location = response.headers.get("location");
  if (!location) {
    return null;
  }

  const resolvedLocation = new URL(location, targetUrl);
  if (resolvedLocation.origin !== targetUrl.origin) {
    return null;
  }

  const upstreamBasePath = new URL(getBaseUrl(kind)).pathname.replace(/\/$/, "");
  let proxiedPath = resolvedLocation.pathname;
  if (upstreamBasePath && proxiedPath.startsWith(upstreamBasePath)) {
    proxiedPath = proxiedPath.slice(upstreamBasePath.length) || "/";
  }

  return `${getProxyPrefix(kind)}${proxiedPath}${resolvedLocation.search}${resolvedLocation.hash}`;
}

function buildRequestHeaders(kind: ProxyKind, request: NextRequest): Headers {
  const headers = new Headers();
  const allowed = requestHeaderAllowlist[kind];

  for (const [key, value] of request.headers.entries()) {
    const lowerKey = key.toLowerCase();
    if (hopByHopHeaders.has(lowerKey)) {
      continue;
    }
    if (allowed.has(lowerKey)) {
      headers.set(key, value);
    }
  }

  if (kind === "core") {
    const apiKey = process.env.STATELOCK_CORE_API_KEY;
    if (apiKey) {
      headers.set("X-Statelock-Api-Key", apiKey);
    }
  } else {
    const apiKey = process.env.STATELOCK_OBS_API_KEY;
    if (apiKey) {
      headers.set("Authorization", `Bearer ${apiKey}`);
    }
  }

  return headers;
}

function buildResponseHeaders(kind: ProxyKind, response: Response, targetUrl: URL): Headers {
  const headers = new Headers();
  const allowed = responseHeaderAllowlist[kind];

  for (const [key, value] of response.headers.entries()) {
    const lowerKey = key.toLowerCase();
    if (lowerKey === "set-cookie") {
      continue;
    }
    if (allowed.has(lowerKey)) {
      headers.set(key, value);
    }
  }

  const safeLocation = getSafeRedirectLocation(kind, response, targetUrl);
  if (safeLocation) {
    headers.set("location", safeLocation);
  }

  return headers;
}

async function buildBody(request: NextRequest): Promise<BodyInit | undefined> {
  if (request.method === "GET" || request.method === "HEAD") {
    return undefined;
  }

  const contentLength = request.headers.get("content-length");
  if (contentLength === "0") {
    return undefined;
  }

  const body = await request.arrayBuffer();
  if (body.byteLength === 0) {
    return undefined;
  }

  return body;
}

export async function proxyToUpstream(
  kind: ProxyKind,
  request: NextRequest,
  path: string[],
): Promise<Response> {
  try {
    const targetUrl = buildTargetUrl(kind, request, path);
    const upstreamResponse = await fetch(targetUrl, {
      method: request.method,
      headers: buildRequestHeaders(kind, request),
      body: await buildBody(request),
      redirect: "manual",
    });

    return new Response(upstreamResponse.body, {
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText,
      headers: buildResponseHeaders(kind, upstreamResponse, targetUrl),
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unexpected proxy error";
    return NextResponse.json(
      {
        code: "proxy_error",
        message,
      },
      { status: 502 },
    );
  }
}
