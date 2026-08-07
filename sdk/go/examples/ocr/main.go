// IOTYPE_TOKEN=... go run ./examples/ocr contract.pdf
package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"os"

	"github.com/iotype-ai/iotype-api/sdk/go/iotype"
)

func main() {
	if len(os.Args) < 2 {
		log.Fatal("usage: ocr <file.pdf|file.jpg>")
	}

	ctx := context.Background()

	io, err := iotype.New("")
	if err != nil {
		log.Fatal(err)
	}

	file, err := io.OCR(ctx, os.Args[1], true)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("uuid:", file.UUID, "(store this — you can resume after a restart)")

	text, err := io.WaitFor(ctx, file.UUID, "ocr", nil)
	if err != nil {
		var timeout *iotype.TimeoutError
		if errors.As(err, &timeout) {
			fmt.Printf("still processing; resume with WaitFor(%q)\n", timeout.UUID)
			return
		}
		log.Fatal(err)
	}

	fmt.Println("\n--- extracted text ---")
	fmt.Println(text)

	if final, err := io.Track(ctx, file.UUID); err == nil {
		if summary, ok := final.Result("summarize"); ok {
			fmt.Println("\n--- summary ---")
			fmt.Println(summary)
		}
	}
}
