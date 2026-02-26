"""Call API Routes — Voice call management and WebSocket streaming.

Endpoints:
- POST   /call/initiate     — Start a new call session
- POST   /call/{id}/audio   — Process an audio chunk
- POST   /call/{id}/text    — Process a text message (WhatsApp/widget)
- POST   /call/{id}/end     — End a call session
- GET    /call/{id}/status  — Get call session status
- WS     /call/ws/{id}      — Real-time WebSocket streaming
"""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import structlog

from config import settings
from core.orchestrator import orchestrator
from models.database import CallDirection, ChannelType

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/call/initiate")
async def initiate_call(
    phone_number: str = Form(...),
    direction: str = Form("inbound"),
    channel: str = Form("voice"),
):
    """Start a new call session.

    Returns session_id and initial greeting to be played.
    """
    try:
        dir_enum = CallDirection(direction)
    except ValueError:
        dir_enum = CallDirection.INBOUND

    try:
        ch_enum = ChannelType(channel)
    except ValueError:
        ch_enum = ChannelType.VOICE

    session = await orchestrator.start_session(
        phone_number=phone_number,
        direction=dir_enum,
        channel=ch_enum,
    )

    return {
        "session_id": session.session_id,
        "status": "active",
        "language": session.language,
        "customer_id": session.customer_id,
        "greeting": "Namaste! VaakAI mein aapka swagat hai. Main aapki kaise madad kar sakta hoon?",
    }


@router.post("/call/{session_id}/audio")
async def process_audio(
    session_id: str,
    audio: UploadFile = File(...),
):
    """Process an audio chunk through the full pipeline.

    Accepts audio file upload (WAV/PCM) and returns:
    - Transcribed text
    - Bot response text
    - Audio response (base64 or binary)
    - Intent, emotion, fraud scores
    """
    audio_data = await audio.read()

    result = await orchestrator.process_audio(session_id, audio_data)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    # Remove binary audio from JSON response (sent separately or base64 encoded)
    response = {k: v for k, v in result.items() if k not in ("audio_response", "backchannel_audio")}

    return response


@router.post("/call/{session_id}/text")
async def process_text(
    session_id: str,
    text: str = Form(...),
):
    """Process a text message (for WhatsApp/widget channels)."""
    result = await orchestrator.process_text(session_id, text)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.post("/call/{session_id}/end")
async def end_call(
    session_id: str,
    reason: str = Form("normal"),
):
    """End a call session and trigger post-call processing."""
    result = await orchestrator.end_session(session_id, reason)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/call/{session_id}/status")
async def call_status(session_id: str):
    """Get current status of a call session."""
    session = orchestrator._sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "is_active": session.is_active,
        "language": session.language,
        "turn_index": session.turn_index,
        "phone": session.phone_number,
        "channel": session.channel.value,
    }


@router.websocket("/call/ws/{session_id}")
async def websocket_stream(websocket: WebSocket, session_id: str):
    """Real-time WebSocket endpoint for streaming audio.

    Protocol:
    - Client sends binary audio frames
    - Server responds with JSON control messages and binary audio
    - Messages have a 'type' field: 'transcript', 'response', 'backchannel', 'status'
    """
    await websocket.accept()
    logger.info("ws_connected", session_id=session_id)

    try:
        while True:
            # Receive audio frame from client
            data = await websocket.receive()

            if "bytes" in data:
                audio_data = data["bytes"]

                # Process through pipeline
                result = await orchestrator.process_audio(session_id, audio_data)

                if "error" in result:
                    await websocket.send_json({
                        "type": "error",
                        "message": result["error"],
                    })
                    continue

                # Send backchannel immediately if available
                if result.get("backchannel_audio"):
                    await websocket.send_json({
                        "type": "backchannel",
                        "text": result.get("backchannel_text", ""),
                    })
                    await websocket.send_bytes(result["backchannel_audio"])

                # Send transcript
                if result.get("user_text"):
                    await websocket.send_json({
                        "type": "transcript",
                        "text": result["user_text"],
                        "language": result.get("language"),
                        "intent": result.get("intent", {}).get("intent"),
                        "emotion": result.get("emotion", {}).get("emotion"),
                    })

                # Send bot response
                if result.get("bot_response"):
                    await websocket.send_json({
                        "type": "response",
                        "text": result["bot_response"],
                        "latency_ms": result.get("latency_ms"),
                    })

                    # Send audio response
                    if result.get("audio_response"):
                        await websocket.send_bytes(result["audio_response"])

                # Send status if escalated
                if result.get("status") == "escalated":
                    await websocket.send_json({
                        "type": "escalated",
                        "reason": result.get("reason"),
                    })

            elif "text" in data:
                # Handle text messages (for widget/chat mode)
                msg = json.loads(data["text"])

                if msg.get("type") == "text":
                    result = await orchestrator.process_text(
                        session_id, msg.get("text", "")
                    )
                    await websocket.send_json({
                        "type": "response",
                        **{k: v for k, v in result.items() if k != "error"},
                    })

                elif msg.get("type") == "end":
                    result = await orchestrator.end_session(session_id)
                    await websocket.send_json({
                        "type": "session_ended",
                        **result,
                    })
                    break

    except WebSocketDisconnect:
        logger.info("ws_disconnected", session_id=session_id)
        await orchestrator.end_session(session_id, reason="websocket_disconnect")
    except Exception as e:
        logger.error("ws_error", session_id=session_id, error=str(e))
        await orchestrator.end_session(session_id, reason="error")


# WhatsApp webhook
@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request_data: dict):
    """Handle incoming WhatsApp messages via Meta webhook."""
    from integrations.whatsapp.meta_cloud import whatsapp_client

    parsed = whatsapp_client.parse_webhook(request_data)
    if not parsed:
        return {"status": "no_message"}

    phone = parsed.get("from", "")
    text = parsed.get("text", "")

    if not text:
        return {"status": "unsupported_message_type"}

    # Mark as read
    if parsed.get("message_id"):
        await whatsapp_client.mark_as_read(parsed["message_id"])

    # Get or create session for this WhatsApp user
    session_key = f"wa_{phone}"
    session = orchestrator._sessions.get(session_key)

    if not session:
        session = await orchestrator.start_session(
            phone_number=phone,
            channel=ChannelType.WHATSAPP,
        )
        # Re-map with WhatsApp-specific key
        orchestrator._sessions[session_key] = session

    # Process the text message
    result = await orchestrator.process_text(session.session_id, text)

    # Send response back via WhatsApp
    if result.get("bot_response"):
        await whatsapp_client.send_text(phone, result["bot_response"])

    return {"status": "processed", "session_id": session.session_id}


@router.get("/whatsapp/webhook")
async def whatsapp_verify(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = ""):
    """WhatsApp webhook verification (GET request from Meta)."""
    verify_token = settings.whatsapp_verify_token or "vaakai_verify"
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        return int(hub_challenge) if hub_challenge.isdigit() else hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")
