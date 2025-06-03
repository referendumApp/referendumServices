FROM node:18-alpine

WORKDIR /app

RUN apk add --no-cache git

COPY package*.json yarn.lock ./
COPY packages/ ./packages/

RUN yarn install --frozen-lockfile --ignore-scripts

COPY . .

RUN yarn build

EXPOSE 2582

WORKDIR /app/packages/server

CMD ["yarn", "run", "start"]
