Fill variable TOKEN in docker-compose.yml and enter the command in terminal:

```
docker-compose up
```
That`s it

For additional configurate you can fill other fields in environment in docker-compose.yml:
```
  bot:
    ports:
      - "80:80"
    depends_on:
      - redis
      - api
    build:
      context: client
    environment:
      TOKEN: BOT_TOKEN
      JWT: 9565157d0e36f3e9c1c334666899186f3d1aaa5b3fbee105412c4344cd83b1e8
    ->SMTP_PASSWORD: my_smtp_password
    ->ORGANIZATION_EMAIL: my_email
      API_KEY: my_api_key
      CIPHER: 0hVakjHd7dL07Ndtb0wTcaJQPx2HwlAgpbIQzhW2rEU=
    ->GROUP_ID: my_group_id
      BACKEND: http://api:8000
      REDIS_HOST: redis
      REDIS_PORT: 6379
```
valid SMTP_PASSWORD and ORGANIZATION_EMAIL will allow setting the user's email and resetting the password<br>
The bot must be in the specified GROUP ID