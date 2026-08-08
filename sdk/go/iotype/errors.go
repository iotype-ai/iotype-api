package iotype

import (
	"encoding/json"
	"fmt"
	"time"
)

// APIError is the base error returned by this package. Use errors.As to
// inspect the HTTP status.
//
// It is deliberately not named Error: embedding a type called Error would
// create a field of that name in every subtype, shadowing the promoted
// Error() method and breaking the error interface.
type APIError struct {
	Status  int
	Message string
	Body    map[string]any
}

func (e *APIError) Error() string {
	if e.Status != 0 {
		return fmt.Sprintf("iotype: [%d] %s", e.Status, e.Message)
	}
	return "iotype: " + e.Message
}

// AuthError is returned for HTTP 401.
//
// The upstream docs list four causes for this single status: a missing
// Authorization header, a malformed token, an expired token, or an exhausted
// token balance. Mention the balance case when surfacing this to a user.
type AuthError struct{ *APIError }

// InsufficientTokensError means the token balance is exhausted.
// The status code is inferred, not documented.
type InsufficientTokensError struct{ *APIError }

// ValidationError is returned for HTTP 422. Status code inferred.
type ValidationError struct{ *APIError }

// NotFoundError is returned for HTTP 404 — unknown uuid. Status code inferred.
type NotFoundError struct{ *APIError }

// PayloadTooLargeError is returned for HTTP 413. Status code inferred.
type PayloadTooLargeError struct{ *APIError }

// RateLimitError is returned for HTTP 429. Status code inferred.
type RateLimitError struct{ *APIError }

// ServerError is returned for HTTP 5xx. Safe to retry with backoff.
type ServerError struct{ *APIError }

// TimeoutError means an asynchronous job did not finish within the deadline.
//
// The job is still running server-side. Keep the UUID and resume tracking with
// WaitFor rather than re-uploading, which would be billed again.
type TimeoutError struct {
	UUID   string
	Waited time.Duration
}

func (e *TimeoutError) Error() string {
	return fmt.Sprintf(
		"iotype: file %s did not finish within %s; it is still processing — "+
			"resume with WaitFor rather than re-uploading",
		e.UUID, e.Waited,
	)
}

// RealtimeError means the realtime ASR WebSocket session failed.
type RealtimeError struct{ *APIError }

func errorForStatus(status int, raw []byte) error {
	if status >= 200 && status < 300 {
		return nil
	}

	base := &APIError{Status: status, Message: truncate(raw, 500)}

	var parsed map[string]any
	if json.Unmarshal(raw, &parsed) == nil {
		base.Body = parsed
		if m, ok := parsed["message"].(string); ok && m != "" {
			base.Message = m
		} else if m, ok := parsed["error"].(string); ok && m != "" {
			base.Message = m
		}
	}

	if status >= 500 {
		return &ServerError{base}
	}

	switch status {
	case 401:
		base.Message += " — the token is missing, malformed, expired, or its balance is exhausted."
		return &AuthError{base}
	case 402:
		return &InsufficientTokensError{base}
	case 404:
		return &NotFoundError{base}
	case 413:
		return &PayloadTooLargeError{base}
	case 422:
		return &ValidationError{base}
	case 429:
		return &RateLimitError{base}
	default:
		return base
	}
}
