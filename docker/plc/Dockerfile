FROM node:18-alpine

WORKDIR /app

# Install git (needed for some yarn dependencies)
RUN apk add --no-cache git

# Copy package files
COPY package*.json yarn.lock ./
COPY packages/ ./packages/

# Install dependencies without running build scripts
RUN yarn install --frozen-lockfile --ignore-scripts

# Copy the rest of the source code
COPY . .

# Now run the build
RUN yarn build

# Expose port (adjust if different)
EXPOSE 2582

# Change to server directory and start
WORKDIR /app/packages/server

# Start the server from the packages/server directory
CMD ["yarn", "run", "start"]
