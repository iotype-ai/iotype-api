class StreamingResampler {
  constructor(inputRate, outputRate) { this.ratio = inputRate / outputRate; this.position = 0; this.tail = new Float32Array(0); }
  process(input) {
    const data = new Float32Array(this.tail.length + input.length); data.set(this.tail); data.set(input, this.tail.length);
    const output = [];
    while (this.position + 1 < data.length) { const left = Math.floor(this.position); const fraction = this.position - left; output.push(data[left] + (data[left + 1] - data[left]) * fraction); this.position += this.ratio; }
    this.position -= data.length - 1; this.tail = data.slice(-1); return Float32Array.from(output);
  }
}
function float32ToPcm16(samples) { const buffer = new ArrayBuffer(samples.length * 2); const view = new DataView(buffer); for (let i = 0; i < samples.length; i += 1) { const s = Math.max(-1, Math.min(1, samples[i])); view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true); } return buffer; }
