// IOTYPE_TOKEN=... go run ./examples/quickstart
package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/iotype-ai/iotype-api/sdk/go/iotype"
)

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	io, err := iotype.New("")
	if err != nil {
		log.Fatal(err)
	}

	text, err := io.Translate(ctx, "سلام! امروز هوا بسیار عالی است.", iotype.Persian, iotype.English)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("translate:", text)

	url, err := io.Synthesize(ctx, "سلام دنیا", &iotype.SynthesizeOptions{Speaker: "tanaz"})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("synthesize:", url)

	files, err := io.Files(ctx)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("files: %d submitted\n", len(files))
	for i, f := range files {
		if i >= 5 {
			break
		}
		fmt.Printf("  %s  %s  done=%v\n", f.UUID, f.Filename, f.Done())
	}
}
