// Package iotype is the official Go client for iotype — Persian, English and
// Arabic speech recognition, OCR, translation and text-to-speech.
//
//	io, err := iotype.New("")            // reads IOTYPE_TOKEN
//	out, err := io.Translate(ctx, "سلام دنیا", "fa", "en")
//
// Get an API token at https://iotype.com/api-service/authentication and read
// the service documentation at https://iotype.com/api-service.
package iotype

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

const (
	// DefaultBaseURL is the production host.
	DefaultBaseURL = "https://iotype.com"
	// DefaultTimeout is the per-request timeout.
	DefaultTimeout = 120 * time.Second
	// SampleRate is the recommended audio sample rate for realtime ASR.
	SampleRate = 16000
)

// Language is an ISO 639-1 code accepted by the API.
type Language string

const (
	Persian Language = "fa"
	English Language = "en"
	Arabic  Language = "ar"
)

// Model selects the realtime recognition model.
type Model string

const (
	ModelPersian Model = "io-fa"
	ModelEnglish Model = "io-en"
	ModelArabic  Model = "io-ar"
)

// Tone is the delivery style for synthesised speech.
type Tone string

const (
	ToneGeneral Tone = "general"
	ToneFormal  Tone = "formal"
)

// TokenType distinguishes a long-lived access token from a short-lived,
// single-use flash token.
type TokenType string

const (
	AccessToken TokenType = "access_token"
	FlashToken  TokenType = "flash_token"
)

// Speakers lists every available text-to-speech voice.
var Speakers = []string{
	"behrooz", "mehran", "farshid", "sara", "mitra", "siavash",
	"shirin", "kaveh", "amir", "tanaz", "mahsa",
}

var retryStatuses = map[int]bool{
	408: true, 429: true, 500: true, 502: true, 503: true, 504: true,
}

// Process is one unit of work running on an uploaded file.
type Process struct {
	Type string `json:"type"`
	// Status is not enumerated upstream. Do not branch on it — use
	// Result != nil as the completion signal.
	Status string  `json:"status"`
	Result *string `json:"result"`
}

// Done reports whether the process has produced a result.
func (p Process) Done() bool { return p.Result != nil }

// File is an uploaded file and the processes running on it.
type File struct {
	UUID      string    `json:"uuid"`
	Name      string    `json:"name"`
	Filename  string    `json:"filename"`
	Processes []Process `json:"processes"`
}

// Result returns the first finished result, optionally filtered by process
// type. Always match by type rather than by slice position — when
// summarisation is requested there is more than one process and the order is
// not guaranteed.
func (f File) Result(processType string) (string, bool) {
	for _, p := range f.Processes {
		if processType != "" && p.Type != processType {
			continue
		}
		if p.Done() {
			return *p.Result, true
		}
	}
	return "", false
}

// Results returns every finished result, keyed by process type.
func (f File) Results() map[string]string {
	out := make(map[string]string, len(f.Processes))
	for i, p := range f.Processes {
		if p.Done() {
			key := p.Type
			if key == "" {
				key = fmt.Sprintf("process_%d", i)
			}
			out[key] = *p.Result
		}
	}
	return out
}

// Done reports whether every process has produced a result.
func (f File) Done() bool {
	if len(f.Processes) == 0 {
		return false
	}
	for _, p := range f.Processes {
		if !p.Done() {
			return false
		}
	}
	return true
}

// Client talks to the iotype HTTP API. It is safe for concurrent use.
type Client struct {
	token      string
	baseURL    string
	httpClient *http.Client
	maxRetries int
}

// Option configures a Client.
type Option func(*Client)

// WithBaseURL overrides the API host.
func WithBaseURL(u string) Option {
	return func(c *Client) { c.baseURL = strings.TrimRight(u, "/") }
}

// WithHTTPClient supplies a custom *http.Client, e.g. one with a proxy.
func WithHTTPClient(h *http.Client) Option {
	return func(c *Client) { c.httpClient = h }
}

// WithMaxRetries sets the number of attempts for transient failures.
func WithMaxRetries(n int) Option {
	return func(c *Client) { c.maxRetries = n }
}

// New creates a client. An empty token falls back to $IOTYPE_TOKEN.
func New(token string, opts ...Option) (*Client, error) {
	if token == "" {
		token = os.Getenv("IOTYPE_TOKEN")
	}
	if token == "" {
		return nil, &Error{Message: "no token: pass one to New or set IOTYPE_TOKEN. " +
			"Generate one at https://iotype.com/api-service/authentication"}
	}

	base := os.Getenv("IOTYPE_BASE_URL")
	if base == "" {
		base = DefaultBaseURL
	}

	c := &Client{
		token:      token,
		baseURL:    strings.TrimRight(base, "/"),
		httpClient: &http.Client{Timeout: DefaultTimeout},
		maxRetries: 3,
	}
	for _, opt := range opts {
		opt(c)
	}
	return c, nil
}

// ---------------------------------------------------------------- synchronous

// Translate converts text between fa, en and ar.
func (c *Client) Translate(ctx context.Context, text string, from, to Language) (string, error) {
	var out struct {
		Result string `json:"result"`
	}
	err := c.postJSON(ctx, "/io/v1/translate", map[string]any{
		"source_lang":      string(from),
		"destination_lang": string(to),
		"text":             text,
	}, &out)
	return out.Result, err
}

// SynthesizeOptions configures text-to-speech.
type SynthesizeOptions struct {
	Speaker string // default "tanaz"; see Speakers
	Tone    Tone   // default ToneGeneral
}

// Synthesize generates speech from text and returns the URL of the MP3.
//
// Retention of generated files is not published upstream — download the file
// if you need it long-term.
func (c *Client) Synthesize(ctx context.Context, text string, opts *SynthesizeOptions) (string, error) {
	speaker, tone := "tanaz", ToneGeneral
	if opts != nil {
		if opts.Speaker != "" {
			speaker = opts.Speaker
		}
		if opts.Tone != "" {
			tone = opts.Tone
		}
	}

	valid := false
	for _, s := range Speakers {
		if s == speaker {
			valid = true
			break
		}
	}
	if !valid {
		return "", &Error{Message: fmt.Sprintf("unknown speaker %q; valid: %s",
			speaker, strings.Join(Speakers, ", "))}
	}

	var out struct {
		URL string `json:"url"`
	}
	err := c.postJSON(ctx, "/io/v1/synthesis", map[string]any{
		"tone": string(tone), "speaker": speaker, "text": text,
	}, &out)
	return out.URL, err
}

// TranscribeInstant transcribes a short MP3 synchronously.
//
// For long recordings use Transcribe, which is slower but more accurate.
func (c *Client) TranscribeInstant(ctx context.Context, path string) (string, error) {
	var out struct {
		Result string `json:"result"`
	}
	err := c.postMultipart(ctx, "/io/v1/transcribe/instant", path, nil, &out)
	return out.Result, err
}

// --------------------------------------------------------------- asynchronous

// TranscribeOptions configures file transcription.
type TranscribeOptions struct {
	Summarize  bool
	SourceLang Language
}

// Transcribe uploads an MP3 for high-accuracy transcription.
//
// This endpoint is asynchronous: it returns a File handle, not the transcript.
// Pass the returned UUID to WaitFor to poll for the result.
func (c *Client) Transcribe(ctx context.Context, path string, opts *TranscribeOptions) (File, error) {
	fields := map[string]string{"should_summarize": "false"}
	if opts != nil {
		fields["should_summarize"] = strconv.FormatBool(opts.Summarize)
		if opts.SourceLang != "" {
			fields["source_lang"] = string(opts.SourceLang)
		}
	}

	var out struct {
		File File `json:"file"`
	}
	err := c.postMultipart(ctx, "/io/v1/transcribe", path, fields, &out)
	return out.File, err
}

// TranscribeAndWait uploads an MP3 and blocks until the transcript is ready.
func (c *Client) TranscribeAndWait(ctx context.Context, path string, opts *TranscribeOptions) (string, error) {
	file, err := c.Transcribe(ctx, path, opts)
	if err != nil {
		return "", err
	}
	return c.WaitFor(ctx, file.UUID, "transcribe", nil)
}

// OCR uploads a PDF or JPG for text extraction.
//
// This endpoint is asynchronous: it returns a File handle, not the text.
func (c *Client) OCR(ctx context.Context, path string, summarize bool) (File, error) {
	var out struct {
		File File `json:"file"`
	}
	err := c.postMultipart(ctx, "/io/v1/ocr", path, map[string]string{
		"should_summarize": strconv.FormatBool(summarize),
	}, &out)
	return out.File, err
}

// OCRAndWait uploads a document and blocks until the text is ready.
func (c *Client) OCRAndWait(ctx context.Context, path string, summarize bool) (string, error) {
	file, err := c.OCR(ctx, path, summarize)
	if err != nil {
		return "", err
	}
	return c.WaitFor(ctx, file.UUID, "ocr", nil)
}

// ---------------------------------------------------------------------- files

// Files lists every file submitted with this token.
func (c *Client) Files(ctx context.Context) ([]File, error) {
	var out struct {
		Files []File `json:"files"`
	}
	err := c.postJSON(ctx, "/io/v1/files", map[string]any{}, &out)
	return out.Files, err
}

// Track fetches the current state of one file.
func (c *Client) Track(ctx context.Context, uuid string) (File, error) {
	var out struct {
		File File `json:"file"`
	}
	err := c.postJSON(ctx, "/io/v1/file/track", map[string]any{"uuid": uuid}, &out)
	return out.File, err
}

// PollOptions tunes WaitFor. A nil value uses 5s → 60s backoff over 30 minutes.
type PollOptions struct {
	Timeout         time.Duration
	InitialInterval time.Duration
	MaxInterval     time.Duration
}

// WaitFor polls uuid until a process carries a result, then returns it.
//
// Completion is detected by Result != nil, not by Status — the status
// vocabulary is not published upstream.
//
// On timeout it returns *TimeoutError carrying the UUID. The job keeps running
// server-side; resume with the same UUID rather than re-uploading, which would
// be billed again.
func (c *Client) WaitFor(ctx context.Context, uuid, processType string, opts *PollOptions) (string, error) {
	if uuid == "" {
		return "", &Error{Message: "no uuid to track: the upload response had no file.uuid"}
	}

	timeout, interval, maxInterval := 30*time.Minute, 5*time.Second, 60*time.Second
	if opts != nil {
		if opts.Timeout > 0 {
			timeout = opts.Timeout
		}
		if opts.InitialInterval > 0 {
			interval = opts.InitialInterval
		}
		if opts.MaxInterval > 0 {
			maxInterval = opts.MaxInterval
		}
	}

	deadline := time.Now().Add(timeout)

	for {
		file, err := c.Track(ctx, uuid)
		if err != nil {
			return "", err
		}
		if result, ok := file.Result(processType); ok {
			return result, nil
		}

		if time.Now().After(deadline) {
			return "", &TimeoutError{UUID: uuid, Waited: timeout}
		}

		select {
		case <-ctx.Done():
			return "", ctx.Err()
		case <-time.After(interval):
		}

		if interval *= 2; interval > maxInterval {
			interval = maxInterval
		}
	}
}

// Download saves a generated file, e.g. the MP3 returned by Synthesize.
func (c *Client) Download(ctx context.Context, url, dest string) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return err
	}
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		return &Error{Status: resp.StatusCode, Message: "download failed"}
	}

	f, err := os.Create(dest)
	if err != nil {
		return err
	}
	defer f.Close()

	_, err = io.Copy(f, resp.Body)
	return err
}

// ------------------------------------------------------------------ internals

func (c *Client) postJSON(ctx context.Context, path string, payload any, out any) error {
	body, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	return c.do(ctx, path, func() (io.Reader, string) {
		return bytes.NewReader(body), "application/json"
	}, out)
}

func (c *Client) postMultipart(ctx context.Context, path, filePath string, fields map[string]string, out any) error {
	if _, err := os.Stat(filePath); err != nil {
		return &Error{Message: fmt.Sprintf("file not found: %s", filePath)}
	}

	build := func() (io.Reader, string) {
		var buf bytes.Buffer
		w := multipart.NewWriter(&buf)

		for k, v := range fields {
			_ = w.WriteField(k, v)
		}

		f, err := os.Open(filePath)
		if err == nil {
			defer f.Close()
			if part, perr := w.CreateFormFile("file", filepath.Base(filePath)); perr == nil {
				_, _ = io.Copy(part, f)
			}
		}
		_ = w.Close()

		// FormDataContentType carries the boundary — never set it by hand.
		return &buf, w.FormDataContentType()
	}

	return c.do(ctx, path, build, out)
}

func (c *Client) do(ctx context.Context, path string, build func() (io.Reader, string), out any) error {
	url := c.baseURL + path
	var lastErr error

	for attempt := 0; attempt < c.maxRetries; attempt++ {
		// Rebuild the body each attempt — a reader is consumed by a failed try.
		body, contentType := build()

		req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, body)
		if err != nil {
			return err
		}
		req.Header.Set("Authorization", "Bearer "+c.token)
		req.Header.Set("Accept", "application/json")
		req.Header.Set("X-Requested-With", "XMLHttpRequest")
		req.Header.Set("Content-Type", contentType)

		resp, err := c.httpClient.Do(req)
		if err != nil {
			lastErr = err
			if attempt == c.maxRetries-1 {
				return &Error{Message: fmt.Sprintf("request to %s failed: %v", path, err)}
			}
			backoff(ctx, attempt)
			continue
		}

		raw, readErr := io.ReadAll(resp.Body)
		_ = resp.Body.Close()
		if readErr != nil {
			lastErr = readErr
			if attempt == c.maxRetries-1 {
				return readErr
			}
			backoff(ctx, attempt)
			continue
		}

		if retryStatuses[resp.StatusCode] && attempt < c.maxRetries-1 {
			backoff(ctx, attempt)
			continue
		}

		if err := errorForStatus(resp.StatusCode, raw); err != nil {
			return err
		}
		if out == nil {
			return nil
		}
		if err := json.Unmarshal(raw, out); err != nil {
			return &Error{
				Status:  resp.StatusCode,
				Message: fmt.Sprintf("%s returned an unparseable body: %s", path, truncate(raw, 200)),
			}
		}
		return nil
	}

	return &Error{Message: fmt.Sprintf("request to %s failed after %d attempts: %v", path, c.maxRetries, lastErr)}
}

func backoff(ctx context.Context, attempt int) {
	d := time.Duration(1<<uint(attempt)) * time.Second
	if d > 8*time.Second {
		d = 8 * time.Second
	}
	d += time.Duration(rand.Intn(250)) * time.Millisecond
	select {
	case <-ctx.Done():
	case <-time.After(d):
	}
}

func truncate(b []byte, n int) string {
	if len(b) <= n {
		return string(b)
	}
	return string(b[:n])
}
