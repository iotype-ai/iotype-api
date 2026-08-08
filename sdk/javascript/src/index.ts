/**
 * Official JavaScript/TypeScript SDK for the iotype API.
 *
 * ```ts
 * import { Iotype } from "@iotype-ai/sdk";
 *
 * const io = new Iotype();               // reads IOTYPE_TOKEN in Node
 * await io.translate("سلام دنیا", "fa", "en");
 * ```
 */

export type Language = "fa" | "en" | "ar";
export type Tone = "general" | "formal";
export type Model = "io-fa" | "io-en" | "io-ar";
export type TokenType = "access_token" | "flash_token";

export const SPEAKERS = [
  "behrooz", "mehran", "farshid", "sara", "mitra", "siavash",
  "shirin", "kaveh", "amir", "tanaz", "mahsa",
] as const;
export type Speaker = (typeof SPEAKERS)[number];

/**
 * Frame duration used when slicing audio, in seconds.
 *
 * There is deliberately no SAMPLE_RATE constant — the server dictates the rate
 * in its authorization reply. Read `session.sampleRate` after connecting.
 */
export const FRAME_SECONDS = 0.02;

export interface Process {
  type?: string;
  /**
   * Not enumerated upstream. Do not branch on this — use `result != null`
   * as the completion signal.
   */
  status?: string;
  result?: string | null;
}

export interface IotypeFile {
  uuid?: string;
  name?: string;
  filename?: string;
  processes?: Process[];
}

// ---------------------------------------------------------------------- errors

export class IotypeError extends Error {
  readonly status?: number;
  readonly body?: unknown;

  constructor(message: string, status?: number, body?: unknown) {
    super(status ? `[${status}] ${message}` : message);
    this.name = "IotypeError";
    this.status = status;
    this.body = body;
  }
}

/**
 * HTTP 401. Covers four upstream causes: missing header, malformed token,
 * expired token, **or exhausted token balance**. Mention the balance case
 * when surfacing this to a user.
 */
export class AuthenticationError extends IotypeError {
  constructor(m: string, s?: number, b?: unknown) { super(m, s, b); this.name = "AuthenticationError"; }
}
export class InsufficientTokensError extends IotypeError {
  constructor(m: string, s?: number, b?: unknown) { super(m, s, b); this.name = "InsufficientTokensError"; }
}
export class ValidationError extends IotypeError {
  constructor(m: string, s?: number, b?: unknown) { super(m, s, b); this.name = "ValidationError"; }
}
export class NotFoundError extends IotypeError {
  constructor(m: string, s?: number, b?: unknown) { super(m, s, b); this.name = "NotFoundError"; }
}
export class RateLimitError extends IotypeError {
  constructor(m: string, s?: number, b?: unknown) { super(m, s, b); this.name = "RateLimitError"; }
}
export class ServerError extends IotypeError {
  constructor(m: string, s?: number, b?: unknown) { super(m, s, b); this.name = "ServerError"; }
}

/**
 * An async job did not finish in time. It is still running server-side —
 * keep `uuid` and resume tracking rather than re-uploading, which is billed again.
 */
export class ProcessingTimeout extends IotypeError {
  readonly uuid?: string;
  constructor(message: string, uuid?: string) {
    super(message);
    this.name = "ProcessingTimeout";
    this.uuid = uuid;
  }
}

// --------------------------------------------------------------------- helpers

/** First finished result on a file, optionally filtered by process type. */
export function fileResult(file: IotypeFile, processType?: string): string | null {
  for (const p of file.processes ?? []) {
    if (processType && p.type !== processType) continue;
    if (p.result != null) return p.result;
  }
  return null;
}

/** Every finished result on a file, keyed by process type. */
export function fileResults(file: IotypeFile): Record<string, string> {
  const out: Record<string, string> = {};
  (file.processes ?? []).forEach((p, i) => {
    if (p.result != null) out[p.type ?? `process_${i}`] = p.result;
  });
  return out;
}

const RETRY_STATUSES = new Set([408, 429, 500, 502, 503, 504]);
const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

// ---------------------------------------------------------------------- client

export interface IotypeOptions {
  token?: string;
  baseUrl?: string;
  /** Per-request timeout in milliseconds. Default 120000. */
  timeout?: number;
  /** Attempts for transient failures (429, 5xx, network). Default 3. */
  maxRetries?: number;
  fetch?: typeof globalThis.fetch;
}

export interface AsyncOptions {
  summarize?: boolean;
  /** Poll until the result is ready and return the text directly. */
  wait?: boolean;
  /** Overall polling deadline in milliseconds. Default 1800000 (30 min). */
  timeout?: number;
}

export class Iotype {
  readonly baseUrl: string;
  private readonly token: string;
  private readonly timeout: number;
  private readonly maxRetries: number;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(tokenOrOptions?: string | IotypeOptions) {
    const opts: IotypeOptions =
      typeof tokenOrOptions === "string" ? { token: tokenOrOptions } : tokenOrOptions ?? {};

    const env = typeof process !== "undefined" ? process.env : undefined;

    this.token = opts.token ?? env?.IOTYPE_TOKEN ?? "";
    if (!this.token) {
      throw new IotypeError(
        "No token. Pass one to the constructor or set IOTYPE_TOKEN. " +
          "Generate one at https://iotype.com/api-service/authentication",
      );
    }

    this.baseUrl = (opts.baseUrl ?? env?.IOTYPE_BASE_URL ?? "https://iotype.com").replace(/\/+$/, "");
    this.timeout = opts.timeout ?? 120_000;
    this.maxRetries = opts.maxRetries ?? 3;
    this.fetchImpl = opts.fetch ?? globalThis.fetch;

    if (!this.fetchImpl) {
      throw new IotypeError("No fetch available. Use Node 18+, or pass { fetch }.");
    }
  }

  // -------------------------------------------------------------- internals

  private headers(json: boolean): Record<string, string> {
    const h: Record<string, string> = {
      Authorization: `Bearer ${this.token}`,
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
    };
    // Never set Content-Type for FormData — the runtime adds the boundary.
    if (json) h["Content-Type"] = "application/json";
    return h;
  }

  private async request<T>(
    path: string,
    body: unknown,
    opts: { timeout?: number } = {},
  ): Promise<T> {
    const isForm = typeof FormData !== "undefined" && body instanceof FormData;
    const url = `${this.baseUrl}${path}`;
    let lastError: unknown;

    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), opts.timeout ?? this.timeout);

      try {
        const response = await this.fetchImpl(url, {
          method: "POST",
          headers: this.headers(!isForm),
          body: isForm ? (body as FormData) : JSON.stringify(body ?? {}),
          signal: controller.signal,
        });

        if (RETRY_STATUSES.has(response.status) && attempt < this.maxRetries - 1) {
          await sleep(Math.min(2 ** attempt, 8) * 1000 + Math.random() * 250);
          continue;
        }

        const text = await response.text();
        let parsed: unknown;
        try { parsed = JSON.parse(text); } catch { parsed = undefined; }

        if (!response.ok) throw toError(response.status, parsed, text);
        if (parsed === undefined) {
          throw new IotypeError(`${path} returned a non-JSON body: ${text.slice(0, 200)}`, response.status);
        }
        return parsed as T;
      } catch (err) {
        if (err instanceof IotypeError) throw err;
        lastError = err;
        if (attempt === this.maxRetries - 1) break;
        await sleep(Math.min(2 ** attempt, 8) * 1000 + Math.random() * 250);
      } finally {
        clearTimeout(timer);
      }
    }

    throw new IotypeError(`Request to ${path} failed after ${this.maxRetries} attempts: ${lastError}`);
  }

  // ------------------------------------------------------------ synchronous

  /** Translate text between `fa`, `en` and `ar`. */
  async translate(text: string, sourceLang: Language, destinationLang: Language): Promise<string> {
    const body = await this.request<{ result?: string }>(
      "/io/v1/translate",
      { source_lang: sourceLang, destination_lang: destinationLang, text },
      { timeout: 30_000 },
    );
    return body.result ?? "";
  }

  /**
   * Generate speech from text. Returns the URL of the resulting MP3.
   * Retention of generated files is not published — download it if you need it.
   */
  async synthesize(
    text: string,
    opts: { speaker?: Speaker; tone?: Tone } = {},
  ): Promise<string> {
    const speaker = opts.speaker ?? "tanaz";
    if (!SPEAKERS.includes(speaker)) {
      throw new IotypeError(`Unknown speaker "${speaker}". Valid: ${SPEAKERS.join(", ")}`);
    }
    const body = await this.request<{ url?: string }>(
      "/io/v1/synthesis",
      { tone: opts.tone ?? "general", speaker, text },
      { timeout: 60_000 },
    );
    return body.url ?? "";
  }

  /** Transcribe a short MP3 synchronously. For long audio use `transcribe()`. */
  async transcribeInstant(file: FileInput, filename = "audio.mp3"): Promise<string> {
    const form = await toFormData(file, filename);
    const body = await this.request<{ result?: string }>("/io/v1/transcribe/instant", form);
    return body.result ?? "";
  }

  // ----------------------------------------------------------- asynchronous

  /**
   * Transcribe an MP3 with high accuracy. **Asynchronous** — returns a file
   * handle unless `wait: true`, in which case it polls and returns the text.
   */
  async transcribe(
    file: FileInput,
    opts: AsyncOptions & { sourceLang?: Language; filename?: string } = {},
  ): Promise<IotypeFile | string> {
    const form = await toFormData(file, opts.filename ?? "audio.mp3");
    form.append("should_summarize", String(Boolean(opts.summarize)));
    if (opts.sourceLang) form.append("source_lang", opts.sourceLang);

    const body = await this.request<{ file?: IotypeFile }>("/io/v1/transcribe", form);
    const uploaded = body.file ?? {};
    if (!opts.wait) return uploaded;
    return this.waitFor(uploaded.uuid, { processType: "transcribe", timeout: opts.timeout });
  }

  /**
   * Extract text from a PDF or JPG. **Asynchronous** — returns a file handle
   * unless `wait: true`, in which case it polls and returns the text.
   */
  async ocr(
    file: FileInput,
    opts: AsyncOptions & { filename?: string } = {},
  ): Promise<IotypeFile | string> {
    const form = await toFormData(file, opts.filename ?? "document.pdf");
    form.append("should_summarize", String(Boolean(opts.summarize)));

    const body = await this.request<{ file?: IotypeFile }>("/io/v1/ocr", form);
    const uploaded = body.file ?? {};
    if (!opts.wait) return uploaded;
    return this.waitFor(uploaded.uuid, { processType: "ocr", timeout: opts.timeout });
  }

  // ------------------------------------------------------------------ files

  /** List every file submitted with this token. */
  async files(): Promise<IotypeFile[]> {
    const body = await this.request<{ files?: IotypeFile[] }>("/io/v1/files", {}, { timeout: 30_000 });
    return body.files ?? [];
  }

  /** Fetch the current state of one file. */
  async track(uuid: string): Promise<IotypeFile> {
    const body = await this.request<{ file?: IotypeFile }>(
      "/io/v1/file/track", { uuid }, { timeout: 30_000 },
    );
    return body.file ?? {};
  }

  /**
   * Poll `uuid` until a process carries a result, then return it.
   *
   * Backoff starts at 5s and doubles to a 60s ceiling. Completion is detected
   * by `result != null`, not by `status`.
   */
  async waitFor(
    uuid: string | undefined,
    opts: { processType?: string; timeout?: number; initialInterval?: number; maxInterval?: number } = {},
  ): Promise<string> {
    if (!uuid) throw new IotypeError("No uuid to track — the upload response had no file.uuid.");

    const deadline = Date.now() + (opts.timeout ?? 1_800_000);
    let interval = opts.initialInterval ?? 5_000;
    const maxInterval = opts.maxInterval ?? 60_000;

    for (;;) {
      const result = fileResult(await this.track(uuid), opts.processType);
      if (result != null) return result;

      if (Date.now() >= deadline) {
        throw new ProcessingTimeout(
          `File ${uuid} did not finish in time. It is still processing — ` +
            "resume with waitFor(uuid) rather than re-uploading.",
          uuid,
        );
      }

      await sleep(Math.min(interval, Math.max(0, deadline - Date.now())));
      interval = Math.min(interval * 2, maxInterval);
    }
  }

  /**
   * Open a realtime ASR session.
   *
   * Defaults to `access_token`. From a browser or mobile app, mint a Flash
   * Token on your server and pass `tokenType: "flash_token"` — never ship an
   * access token to a client.
   */
  realtime(opts: { model?: Model; token?: string; tokenType?: TokenType } = {}): RealtimeSession {
    return new RealtimeSession({
      url: this.baseUrl.replace(/^http/, "ws") + "/socket/realtime",
      token: opts.token ?? this.token,
      tokenType: opts.tokenType ?? "access_token",
      model: opts.model ?? "io-fa",
    });
  }
}

// -------------------------------------------------------------------- realtime

export interface RealtimeEvent {
  type: "partial" | "final" | string;
  text: string;
}

/** The server's reply to the handshake. */
export interface AuthResult {
  status?: "authorized" | string;
  model?: Model;
  /** The rate the server expects audio at. Not a fixed constant. */
  sample_rate?: number;
  error?: string;
}

/**
 * A streaming speech-recognition session.
 *
 * The protocol has four steps, and skipping any of them breaks the session:
 *
 * 1. Send the handshake, nested inside a `config` object.
 * 2. **Wait for the reply.** It carries {@link sampleRate} — the rate you must
 *    resample to. Sending audio before it arrives closes the socket.
 * 3. Stream PCM 16-bit mono little-endian audio as raw binary, 20 ms per frame.
 * 4. Call {@link finish} (or {@link endOfStream}) before closing, or the final
 *    utterance is lost.
 *
 * Never base64-encode the audio.
 *
 * `partial` events are interim and may be revised — render them, never persist
 * them. `final` events are settled — persist those.
 */
export class RealtimeSession {
  private ws?: WebSocket;
  private readonly cfg: { url: string; token: string; tokenType: TokenType; model: Model };

  /**
   * Sample rate the server expects, in Hz. Set by {@link connect}.
   * **Resample your audio to this — do not assume a fixed value.**
   */
  sampleRate?: number;
  /** Model the server selected, echoed back in the authorization reply. */
  negotiatedModel?: Model;

  /** Concatenated final transcript so far. */
  committed = "";
  /** Latest partial, not yet settled. */
  partial = "";

  onPartial?: (text: string) => void;
  onFinal?: (text: string) => void;
  onError?: (err: unknown) => void;
  onClose?: () => void;

  constructor(cfg: { url: string; token: string; tokenType: TokenType; model: Model }) {
    this.cfg = cfg;
  }

  /**
   * Connect, send the handshake, and wait for the server to authorize.
   *
   * Resolves only once `{ status: "authorized" }` has arrived. After that,
   * {@link sampleRate} holds the rate you must resample audio to.
   *
   * @throws IotypeError if the server rejects the token or does not reply.
   */
  async connect(timeoutMs = 30_000): Promise<this> {
    const WS: typeof WebSocket =
      (globalThis as { WebSocket?: typeof WebSocket }).WebSocket ??
      ((await import("ws")) as unknown as { default: typeof WebSocket }).default;

    const ws = new WS(this.cfg.url);
    (ws as { binaryType: string }).binaryType = "arraybuffer";
    this.ws = ws;

    await new Promise<void>((resolve, reject) => {
      ws.addEventListener("open", () => resolve());
      ws.addEventListener("error", () => reject(new IotypeError("WebSocket connection failed.")));
    });

    // Step 1 — handshake. Must be first; audio before this closes the socket.
    // Note the "config" envelope — the fields are nested, not top-level.
    ws.send(JSON.stringify({
      config: {
        model: this.cfg.model,
        type: this.cfg.tokenType,
        token: this.cfg.token,
      },
    }));

    // Step 2 — wait for authorization. It carries the sample rate.
    const auth = await new Promise<AuthResult>((resolve, reject) => {
      const timer = setTimeout(
        () => reject(new IotypeError("No authorization reply from the ASR server.")),
        timeoutMs,
      );
      const onAuth = (event: MessageEvent) => {
        if (typeof event.data !== "string") return;
        let msg: AuthResult;
        try { msg = JSON.parse(event.data); } catch { return; }

        if (msg.error) {
          clearTimeout(timer);
          ws.removeEventListener("message", onAuth);
          reject(new IotypeError(`ASR authorization rejected: ${msg.error}`));
        } else if (msg.status === "authorized") {
          clearTimeout(timer);
          ws.removeEventListener("message", onAuth);
          resolve(msg);
        }
      };
      ws.addEventListener("message", onAuth);
    });

    this.sampleRate = auth.sample_rate;
    this.negotiatedModel = auth.model;

    if (!this.sampleRate) {
      this.close();
      throw new IotypeError(
        "Server did not return a sample_rate; audio cannot be sent without it.",
      );
    }

    // Results. Two shapes, told apart by which key is present — no `type` field.
    ws.addEventListener("message", (event: MessageEvent) => {
      if (typeof event.data !== "string") return;
      let msg: { partial?: string; text?: string };
      try { msg = JSON.parse(event.data); } catch { return; }

      if (typeof msg.partial === "string") {
        this.partial = msg.partial;
        this.onPartial?.(this.partial);
      }
      if (typeof msg.text === "string" && msg.text.trim()) {
        this.committed += msg.text.trim() + " ";
        this.partial = "";
        this.onFinal?.(msg.text.trim());
      }
    });

    ws.addEventListener("error", (e) => this.onError?.(e));
    ws.addEventListener("close", () => this.onClose?.());

    return this;
  }

  /** Samples per 20 ms frame at the negotiated rate. */
  get frameSize(): number {
    if (!this.sampleRate) throw new IotypeError("Not connected — sampleRate is unknown.");
    return Math.round(this.sampleRate / 50);
  }

  /**
   * Send one frame of raw PCM 16-bit mono little-endian audio.
   * The audio must already be at {@link sampleRate}.
   */
  sendAudio(chunk: ArrayBuffer | Uint8Array | Int16Array): void {
    if (!this.ws || this.ws.readyState !== 1) return;
    const buf =
      chunk instanceof ArrayBuffer
        ? chunk
        : (chunk.buffer.slice(chunk.byteOffset, chunk.byteOffset + chunk.byteLength) as ArrayBuffer);
    this.ws.send(buf);
  }

  /**
   * Tell the server no more audio is coming and to flush its decoder.
   *
   * The last final result arrives shortly afterwards, so do not close
   * immediately — {@link close} waits for you if you pass a delay.
   */
  endOfStream(): void {
    if (!this.ws || this.ws.readyState !== 1) return;
    this.ws.send(JSON.stringify({ eof: 1 }));
  }

  /** What to render: settled text plus the current interim text. */
  get text(): string {
    return this.committed + this.partial;
  }

  /**
   * Send `eof`, wait for the last result, then close.
   *
   * Closing without this loses the final utterance.
   */
  async finish(waitMs = 3000): Promise<string> {
    this.endOfStream();
    await sleep(waitMs);
    this.close();
    return this.committed.trim();
  }

  close(): void {
    this.ws?.close();
    this.ws = undefined;
  }
}

/** Convert normalised Float32 samples in [-1, 1] to PCM 16-bit little-endian. */
export function float32ToPcm16(input: Float32Array): Int16Array {
  const out = new Int16Array(input.length);
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i]));
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return out;
}

// --------------------------------------------------------------------- private

type FileInput = string | Blob | Uint8Array | ArrayBuffer;

async function toFormData(file: FileInput, filename: string): Promise<FormData> {
  const form = new FormData();

  if (typeof file === "string") {
    // Node: treat the string as a filesystem path.
    const { readFile } = await import("node:fs/promises");
    const { basename } = await import("node:path");
    const bytes = await readFile(file);
    form.append("file", new Blob([bytes]), basename(file));
  } else if (file instanceof Uint8Array) {
    form.append("file", new Blob([new Uint8Array(file)]), filename);
  } else if (file instanceof ArrayBuffer) {
    form.append("file", new Blob([file]), filename);
  } else {
    form.append("file", file, filename);
  }

  return form;
}

function toError(status: number, body: unknown, text: string): IotypeError {
  let message = text.slice(0, 500);
  if (body && typeof body === "object") {
    const b = body as { message?: string; error?: string };
    message = b.message ?? b.error ?? message;
  }

  switch (status) {
    case 401:
      return new AuthenticationError(
        `${message} — the token is missing, malformed, expired, or its balance is exhausted.`,
        status, body,
      );
    case 402: return new InsufficientTokensError(message, status, body);
    case 404: return new NotFoundError(message, status, body);
    case 422: return new ValidationError(message, status, body);
    case 429: return new RateLimitError(message, status, body);
    default:
      return status >= 500
        ? new ServerError(message, status, body)
        : new IotypeError(message, status, body);
  }
}

export default Iotype;
