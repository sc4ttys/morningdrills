# Use the official Node.js image from the Docker Hub
FROM node:16

# Set the working directory in the container
WORKDIR /app

# Copy the package.json and package-lock.json files
COPY package*.json ./

# Install the dependencies
RUN npm install
RUN npm install react-scripts

# Copy the rest of the application code into the container
COPY . .

# Set environment variables for React
ARG REACT_APP_BACKEND_IP
ENV REACT_APP_BACKEND_IP=$REACT_APP_BACKEND_IP

# Build the app
RUN npm run build

# Serve the app with a static server
RUN npm install -g serve
CMD ["serve", "-s", "build","-p","80"]

# Expose port 80
EXPOSE 80
