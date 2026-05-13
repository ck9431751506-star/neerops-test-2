FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --only=production

# Copy application code
COPY index.js .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:8080/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)}).on('error', (e) => { throw e; })"

# Expose port
EXPOSE 8080

# Start application
ENV PORT=8080
ENV ENVIRONMENT=production
ENV SERVICE_NAME=neerops-test-service

CMD ["npm", "start"]
