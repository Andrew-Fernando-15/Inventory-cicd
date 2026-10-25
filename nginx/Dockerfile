FROM nginx:1.27-alpine

# Remove default nginx welcome page config
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy custom reverse proxy configuration
COPY default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
