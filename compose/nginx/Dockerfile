FROM nginx:1.13-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY ./compose/nginx/server.conf /etc/nginx/conf.d/