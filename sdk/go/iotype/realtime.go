package iotype

import (
	"context"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"math"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

// FrameSeconds is the frame duration used when slicing audio.
//
// There is deliberately no fixed sample-rate constant: the server dictates the
// rate in its authorization reply. Read RealtimeSession.SampleRate.
const FrameSeconds = 0.02

// RealtimeOptions configures a streaming ASR session.
type RealtimeOptions struct {
	Model     Model     // default ModelPersian
	Token     string    // defaults to the client's token
	TokenType TokenType // default AccessToken
	// Timeout for the authorization handshake. Default 30s.
	AuthTimeout time.Duration
}

// authResult is the server's reply to the handshake.
type authResult struct {
	Status     string `json:"status"`
	Model      Model  `json:"model"`
	SampleRate int    `json:"sample_rate"`
	Error      string `json:"error"`
}

// Event is one recognition result from the server.
//
// The wire format uses two different keys rather than a type field —
// {"partial":"..."} for interim text and {"text":"..."} for settled text.
// This type normalises both into one shape.
//
// A "partial" event is interim and may be revised — render it, never persist
// it. A "final" event is settled for that utterance and will not change —
// persist that one. A session produces many finals.
type Event struct {
	Type string // "partial" or "final"
	Text string
}

// RealtimeSession is a streaming speech-recognition session.
//
// The protocol has four steps and skipping any of them breaks the session:
//
//  1. Send the handshake, nested inside a "config" object.
//  2. Wait for the reply. It carries SampleRate — the rate to resample to.
//     Sending audio before it arrives closes the socket.
//  3. Stream PCM 16-bit mono little-endian audio as binary frames, 20 ms each.
//  4. Call Finish (or EndOfStream) before closing, or the last utterance is lost.
//
// Never base64-encode the audio.
type RealtimeSession struct {
	conn *websocket.Conn

	// SampleRate is the rate the server expects audio at, in Hz. Resample to
	// exactly this value — it is not a fixed constant across deployments.
	SampleRate int
	// NegotiatedModel is the model the server selected.
	NegotiatedModel Model

	mu        sync.Mutex
	committed strings.Builder
	partial   string
}

// Realtime opens a streaming ASR session and completes the handshake.
//
// It returns only after the server has authorized the connection, so
// SampleRate is populated on the returned session.
//
// Defaults to AccessToken because this SDK runs server-side. Never ship an
// access token to a browser or mobile client — mint a Flash Token for those
// and pass TokenType: FlashToken.
func (c *Client) Realtime(ctx context.Context, opts *RealtimeOptions) (*RealtimeSession, error) {
	model, token, tokenType := ModelPersian, c.token, AccessToken
	authTimeout := 30 * time.Second
	if opts != nil {
		if opts.Model != "" {
			model = opts.Model
		}
		if opts.Token != "" {
			token = opts.Token
		}
		if opts.TokenType != "" {
			tokenType = opts.TokenType
		}
		if opts.AuthTimeout > 0 {
			authTimeout = opts.AuthTimeout
		}
	}

	url := strings.Replace(strings.Replace(c.baseURL, "https://", "wss://", 1), "http://", "ws://", 1)
	conn, _, err := websocket.DefaultDialer.DialContext(ctx, url+"/socket/realtime", nil)
	if err != nil {
		return nil, &RealtimeError{&Error{Message: "could not open realtime socket: " + err.Error()}}
	}

	// Step 1 — handshake. Must be the first message; the fields are nested
	// inside a "config" envelope, and audio before this closes the connection.
	handshake, _ := json.Marshal(map[string]any{
		"config": map[string]string{
			"model": string(model),
			"type":  string(tokenType),
			"token": token,
		},
	})
	if err := conn.WriteMessage(websocket.TextMessage, handshake); err != nil {
		_ = conn.Close()
		return nil, &RealtimeError{&Error{Message: "handshake failed: " + err.Error()}}
	}

	// Step 2 — wait for authorization before sending any audio.
	_ = conn.SetReadDeadline(time.Now().Add(authTimeout))
	_, raw, err := conn.ReadMessage()
	_ = conn.SetReadDeadline(time.Time{})
	if err != nil {
		_ = conn.Close()
		return nil, &RealtimeError{&Error{Message: "no authorization reply: " + err.Error()}}
	}

	var auth authResult
	if err := json.Unmarshal(raw, &auth); err != nil {
		_ = conn.Close()
		return nil, &RealtimeError{&Error{Message: fmt.Sprintf("unparseable authorization reply: %s", truncate(raw, 200))}}
	}
	if auth.Error != "" {
		_ = conn.Close()
		return nil, &RealtimeError{&Error{Message: "authorization rejected: " + auth.Error}}
	}
	if auth.Status != "authorized" {
		_ = conn.Close()
		return nil, &RealtimeError{&Error{Message: fmt.Sprintf("unexpected authorization reply: %s", truncate(raw, 200))}}
	}
	if auth.SampleRate == 0 {
		_ = conn.Close()
		return nil, &RealtimeError{&Error{Message: "server returned no sample_rate; audio cannot be sent without it"}}
	}

	return &RealtimeSession{
		conn:            conn,
		SampleRate:      auth.SampleRate,
		NegotiatedModel: auth.Model,
	}, nil
}

// FrameSize returns the number of samples in a 20 ms frame at the negotiated rate.
func (s *RealtimeSession) FrameSize() int {
	return int(math.Round(float64(s.SampleRate) * FrameSeconds))
}

// SendAudio sends one frame of raw PCM 16-bit mono little-endian audio.
// The audio must already be at SampleRate.
func (s *RealtimeSession) SendAudio(chunk []byte) error {
	if s.conn == nil {
		return &RealtimeError{&Error{Message: "session is closed"}}
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.conn.WriteMessage(websocket.BinaryMessage, chunk)
}

// EndOfStream tells the server no more audio is coming and to flush its
// decoder. The last final result arrives shortly afterwards, so do not close
// the connection immediately — prefer Finish.
func (s *RealtimeSession) EndOfStream() error {
	if s.conn == nil {
		return nil
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.conn.WriteMessage(websocket.TextMessage, []byte(`{"eof":1}`))
}

// Finish sends eof, waits for the trailing result, then closes.
//
// Closing without this loses the final utterance.
func (s *RealtimeSession) Finish(wait time.Duration) (string, error) {
	if wait <= 0 {
		wait = 3 * time.Second
	}
	if err := s.EndOfStream(); err != nil {
		return s.Transcript(), err
	}
	time.Sleep(wait)
	err := s.Close()
	return s.Transcript(), err
}

// Events returns a channel of recognition results. The channel closes when the
// socket does.
func (s *RealtimeSession) Events() <-chan Event {
	out := make(chan Event, 16)

	go func() {
		defer close(out)
		for {
			msgType, raw, err := s.conn.ReadMessage()
			if err != nil {
				return
			}
			if msgType != websocket.TextMessage {
				continue
			}

			// Two shapes, told apart by which key is present.
			var msg struct {
				Partial *string `json:"partial"`
				Text    *string `json:"text"`
			}
			if json.Unmarshal(raw, &msg) != nil {
				continue
			}

			if msg.Partial != nil {
				s.mu.Lock()
				s.partial = *msg.Partial
				s.mu.Unlock()
				out <- Event{Type: "partial", Text: *msg.Partial}
			}
			if msg.Text != nil {
				text := strings.TrimSpace(*msg.Text)
				if text != "" {
					s.mu.Lock()
					s.committed.WriteString(text)
					s.committed.WriteString(" ")
					s.partial = ""
					s.mu.Unlock()
				}
				out <- Event{Type: "final", Text: text}
			}
		}
	}()

	return out
}

// Text returns what should be rendered: settled text plus the current interim
// text. Appending partials yourself produces duplicated output.
func (s *RealtimeSession) Text() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.committed.String() + s.partial
}

// Transcript returns only the settled text.
func (s *RealtimeSession) Transcript() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	return strings.TrimSpace(s.committed.String())
}

// Close tears down the session. Prefer Finish, which flushes the decoder first.
func (s *RealtimeSession) Close() error {
	if s.conn == nil {
		return nil
	}
	err := s.conn.Close()
	s.conn = nil
	return err
}

// Float32ToPCM16 converts normalised float samples in [-1, 1] to PCM 16-bit
// little-endian bytes, ready to send with SendAudio.
func Float32ToPCM16(samples []float32) []byte {
	out := make([]byte, len(samples)*2)
	for i, sample := range samples {
		s := math.Max(-1, math.Min(1, float64(sample)))
		binary.LittleEndian.PutUint16(out[i*2:], uint16(int16(s*32767)))
	}
	return out
}

// ResampleLinear resamples float samples with linear interpolation, for the
// common case where the capture device runs at one rate and the server asked
// for another.
//
// Linear interpolation is what the reference browser client uses and is
// adequate for speech. For higher audio quality use a dedicated resampler.
func ResampleLinear(samples []float32, inputRate, outputRate int) []float32 {
	if inputRate == outputRate || len(samples) == 0 {
		return samples
	}

	ratio := float64(inputRate) / float64(outputRate)
	target := int(float64(len(samples)) / ratio)
	out := make([]float32, 0, target)

	for pos := 0.0; pos+1 < float64(len(samples)); pos += ratio {
		left := int(pos)
		frac := float32(pos - float64(left))
		out = append(out, samples[left]+(samples[left+1]-samples[left])*frac)
	}
	return out
}
