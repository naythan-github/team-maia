#!/bin/bash
#
# Start Whisper Server - Background daemon for fast dictation
#
# Usage:
#   bash claude/commands/start_whisper_server.sh
#
# This script starts whisper-server with the small model loaded in memory.
# First transcription takes ~5s (model load), subsequent <1s (inference only).

set -e

# Configuration
WHISPER_SERVER="/opt/homebrew/Cellar/whisper-cpp/1.8.0/bin/whisper-server"
MODEL_PATH="$HOME/.maia/whisper-models/ggml-small.bin"
HOST="127.0.0.1"
PORT="8090"
LOG_DIR="$HOME/.maia/logs"
LOG_FILE="$LOG_DIR/whisper-server.log"
PID_FILE="$HOME/.maia/whisper-server.pid"

# Create log directory
mkdir -p "$LOG_DIR"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Whisper server already running (PID: $PID)"
        echo "🌐 Health check: curl http://$HOST:$PORT/health"
        exit 0
    else
        echo "⚠️  Stale PID file found, removing..."
        rm "$PID_FILE"
    fi
fi

# Validate dependencies
if [ ! -f "$WHISPER_SERVER" ]; then
    echo "❌ whisper-server not found at: $WHISPER_SERVER"
    echo "Install: brew install whisper-cpp"
    exit 1
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ Model not found at: $MODEL_PATH"
    echo "Download: curl -L -o $MODEL_PATH https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
    exit 1
fi

# Start server
echo "🚀 Starting Whisper server..."
echo "   Model: $MODEL_PATH"
echo "   Host: $HOST:$PORT"
echo "   Log: $LOG_FILE"

# Start whisper-server in background
nohup "$WHISPER_SERVER" \
    --model "$MODEL_PATH" \
    --host "$HOST" \
    --port "$PORT" \
    --convert \
    > "$LOG_FILE" 2>&1 &

# Save PID
echo $! > "$PID_FILE"

# Wait for server to start
echo "⏳ Waiting for server to start..."
for i in {1..30}; do
    if curl -s "http://$HOST:$PORT/health" > /dev/null 2>&1; then
        echo "✅ Whisper server running (PID: $(cat $PID_FILE))"
        echo "🎤 Ready for dictation!"
        echo ""
        echo "Test transcription:"
        echo "  python3 claude/tools/whisper_dictation_server.py"
        echo ""
        echo "Stop server:"
        echo "  bash claude/commands/stop_whisper_server.sh"
        exit 0
    fi
    sleep 1
done

echo "❌ Server failed to start within 30 seconds"
echo "Check logs: tail -f $LOG_FILE"
exit 1
