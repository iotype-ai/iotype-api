class CaptureProcessor extends AudioWorkletProcessor { process(inputs) { const samples = inputs[0]?.[0]; if (samples?.length) { const copy = new Float32Array(samples); this.port.postMessage(copy, [copy.buffer]); } return true; } }
registerProcessor("capture-processor", CaptureProcessor);
