FROM node:18-alpine

WORKDIR /app

EXPOSE 3000

COPY ../../frontend/package.json package-lock.json ./

RUN npm install --silent

COPY ../../frontend ./

CMD ["npm", "run", "dev"]