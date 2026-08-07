package iotype

import (
	"context"
	"encoding/binary"
	"encoding/json"
	"math"
	"strings"
	"sync"

	"github.com/gorilla/websocket"
)

// RealtimeOptions configures a streaming ASR session.
type RealtimeOptions struct {
	Model     Model     // default ModelPersian
	Token     string    // defaults to the client's token
	TokenType TokenType // default AccessToken
}

// Event is one recognition result from the server.
//
// A "partial" event is interim and may be revised — render it, never persist
// it. A "final" event is settled for that utterance and will not change —
// persist that one. A session produces many finals.
type Event struct {
	Type string `json:"type"` // "partial" or "final"
	Text string `json:"text"`
}

// RealtimeSession is a streaming speech-recognition session.
//
// Audio must be PCM linear 16-bit, mono, little-endian, sent as raw binary
// frames — never base64. 16 kHz is recommended, and the rate you declare must
// match the bytes you send. Send 20–100 ms frames continuously; large
// infrequent frames increase latency and reduce accuracy.
type RealtimeSession struct {
	conn *websocket.Conn

	mu        sync.Mutex
	committed strings.Builder
	partial   string
}

// Realtime opens a streaming ASR session.
//
// Defaults to AccessToken because this SDK runs server-side. Never ship an
// access token to a browser or mobile client — mint a Flash Token for those
// and pass TokenType: FlashToken.
func (c *Client) Realtime(ctx context.Context, opts *RealtimeOptions) (*RealtimeSession, error) {
	model, token, tokenType := ModelPersian, c.token, AccessToken
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
	}

	url := strings.Replace(strings.Replace(c.baseURL, "https://", "wss://", 1), "http://", "ws://", 1)
	conn, _, err := websocket.DefaultDialer.DialContext(ctx, url+"/socket/realtime", nil)
	if err != nil {
		return nil, &RealtimeError{&Error{Message: "could not open realtime socket: " + err.Error()}}
	}

	// The handshake must be the first message on the socket. Sending audio
	// before it causes the server to close the connection.
	// Note the "config" envelope — the fields are nested, not top-level.
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

	return &RealtimeSession{conn: conn}, nil
}

// SendAudio sends one frame of raw PCM 16-bit mono little-endian audio.
func (s *RealtimeSession) SendAudio(chunk []byte) error {
	if s.conn == nil {
		return &RealtimeError{&Error{Message: "session is closed"}}
	}
	return s.conn.WriteMessage(websocket.BinaryMessage, chunk)
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

			var event Event
			if json.Unmarshal(raw, &event) != nil {
				continue
			}

			s.mu.Lock()
			switch event.Type {
			case "partial":
				s.partial = event.Text
			case "final":
				s.committed.WriteString(event.Text)
				s.committed.WriteString(" ")
				s.partial = ""
			}
			s.mu.Unlock()

			out <- event
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

// Close tears down the session.
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
		s := float64(sample)
		s = math.Max(-1, math.Min(1, s))
		binary.LittleEndian.PutUint16(out[i*2:], uint16(int16(s*32767)))
	}
	return out
}
