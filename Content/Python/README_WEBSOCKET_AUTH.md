# WebSocket Authentication for Unreal Engine GenAI Support

This document explains how to use the authentication system for the WebSocket server.

## Overview

The WebSocket server supports token-based authentication. Each client must provide a valid authentication token in the WebSocket handshake request to connect to the server.

## Authentication Flow

1. The server generates a default authentication token on first run
2. The token is stored in `~/.unrealgenai/websocket_auth.json`
3. Clients must include the token in the WebSocket handshake request
4. The server validates the token before accepting the connection

## Using Authentication

### Server Side

The server automatically handles authentication. On first run, it generates a default token and stores it in the authentication file.

You can manage tokens using the Python API:

```python
import websocket_auth as auth

# Get all tokens
tokens = auth.get_auth_tokens()
print(tokens)

# Create a new token
token = auth.create_auth_token("my_client")
print(f"New token: {token}")

# Delete a token
auth.delete_auth_token("my_client")
```

### Client Side

Clients must include the authentication token in the WebSocket handshake request:

```
GET / HTTP/1.1
Host: localhost:9877
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Authorization: Bearer <token>
```

In JavaScript:

```javascript
const socket = new WebSocket('ws://localhost:9877');
socket.setRequestHeader('Authorization', 'Bearer <token>');
```

In Python:

```python
import websocket

# Create a WebSocket connection
ws = websocket.WebSocket()
ws.connect('ws://localhost:9877', header=["Authorization: Bearer <token>"])
```

## Authentication File

The authentication tokens are stored in a JSON file at `~/.unrealgenai/websocket_auth.json`. The file has the following format:

```json
{
  "default": {
    "token": "550e8400-e29b-41d4-a716-446655440000",
    "created": 1616161616.0,
    "expires": 1618753616.0
  },
  "my_client": {
    "token": "550e8400-e29b-41d4-a716-446655440001",
    "created": 1616161616.0,
    "expires": 1618753616.0
  }
}
```

Each token has:
- A name (e.g., "default", "my_client")
- A token value (UUID)
- A creation timestamp
- An expiration timestamp

## Security Considerations

- The authentication tokens are stored in plain text in the authentication file
- The tokens are transmitted in plain text in the WebSocket handshake request
- For production use, consider using HTTPS/WSS to encrypt the connection
- Consider implementing a more secure authentication system for production use

## Disabling Authentication

If you don't want to use authentication, you can delete the authentication file:

```bash
rm ~/.unrealgenai/websocket_auth.json
```

The server will not require authentication if the authentication file doesn't exist or is empty.
