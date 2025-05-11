FROM node:23-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
COPY .npmrc ./
COPY *.quasar ./
COPY public ./public
COPY src ./src
COPY *.js ./
COPY *.ts ./
COPY *.npmrc ./
COPY *.cjs ./
COPY *.conf ./
COPY *.json ./
COPY index.html ./index.html

RUN npm ci

# COPY .env ./
RUN npm run build

FROM nginx:stable-alpine AS production-stage

COPY nginx.conf /etc/nginx/nginx.conf
RUN mkdir /app

COPY --from=build-stage /app/dist/spa /app
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]