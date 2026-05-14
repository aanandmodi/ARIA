FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN apk add --no-cache git
RUN npm install --omit=dev
COPY index.js .
EXPOSE 3001
CMD ["node", "index.js"]
