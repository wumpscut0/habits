For local launch app create .env file and fill it variables:

1. TOKEN=bot token
2. BACKEND=address api from backend
3. REDIS_HOST=redis host
4. REDIS_PORT=redis port
5. SMTP_PASSWORD=smtp email password 
6. ORGANIZATION_EMAIL=organization mail
7. API_KEY=password (that key must be added manually in database on the server)
8. CIPHER=Fernet cryptography cipher (same in .env backend)

launch redis service and backend

If every thing fine, just launch main.py
