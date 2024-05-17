For local launch app create .env file and fill it variables:

1. JWT=jwt token
2. DATABASE=database address connection
3. SERVICE_PASSWORD=hash password third-party service (SERVICE_PASSWORD in .env frontend)
4. CIPHER=Fernet cryptography cipher (same in .env frontend)


1. Launch postgesql service
2. Make SQL to database: insert into service (id, api_key) values ("Psychological", "<API_KEY in .env client>");

If every thing fine, just launch main.py
