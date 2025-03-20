#!/bin/bash

# Voice Analysis Project Runner
# This script starts both the frontend and backend components
# Usage: ./run.sh [dev|prod]

# Default to development mode if no argument is provided
MODE=${1:-dev}

# Define colors for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}  PT Reading Voice Analysis  ${NC}"
echo -e "${BLUE}  Mode: ${YELLOW}${MODE}${BLUE}  ${NC}"
echo -e "${BLUE}=================================${NC}"

# Check if required tools are installed
check_requirements() {
    echo -e "\n${GREEN}Checking requirements...${NC}"

    # Check for Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
        exit 1
    fi

    # Check for Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Error: Node.js is required but not installed.${NC}"
        exit 1
    fi

    # Check for npm
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}Error: npm is required but not installed.${NC}"
        exit 1
    fi

    echo -e "${GREEN}All requirements met!${NC}"
}

# Setup server environment
setup_server() {
    echo -e "\n${GREEN}Setting up server environment...${NC}"

    # Check if .env file exists, if not create from sample
    if [ ! -f "server/.env" ]; then
        echo -e "${YELLOW}Warning: No .env file found in server directory.${NC}"
        if [ -f "server/.env.sample" ]; then
            echo -e "${YELLOW}Creating .env from .env.sample - PLEASE UPDATE WITH YOUR CREDENTIALS${NC}"
            cp server/.env.sample server/.env
        else
            echo -e "${RED}Error: No .env.sample file found. Please create a .env file manually.${NC}"
            exit 1
        fi
    fi

    # Check if Python virtual environment exists
    if [ ! -d "server/venv" ]; then
        echo -e "${YELLOW}Creating Python virtual environment...${NC}"
        python3 -m venv server/venv
    fi

    # Activate virtual environment and install dependencies
    echo -e "${GREEN}Installing server dependencies...${NC}"
    source server/venv/bin/activate
    pip install -r server/requirements.txt
    deactivate

    echo -e "${GREEN}Server setup complete!${NC}"
}

# Setup client environment
setup_client() {
    echo -e "\n${GREEN}Setting up client environment...${NC}"

    # Navigate to client directory and install dependencies
    echo -e "${GREEN}Installing client dependencies...${NC}"
    (cd client && npm install)

    echo -e "${GREEN}Client setup complete!${NC}"
}

# Start the server component
start_server() {
    echo -e "\n${GREEN}Starting server (backend)...${NC}"

    # Set environment variables based on mode
    if [ "$MODE" = "prod" ]; then
        export DEBUG=False
    else
        export DEBUG=True
    fi

    # Activate virtual environment and start server
    source server/venv/bin/activate

    # Start server in background
    python server/app.py &
    SERVER_PID=$!

    echo -e "${GREEN}Server started with PID: ${SERVER_PID}${NC}"
    return $SERVER_PID
}

# Start the client component
start_client() {
    echo -e "\n${GREEN}Starting client (frontend)...${NC}"

    # Navigate to client directory
    cd client

    # Start client based on mode
    if [ "$MODE" = "prod" ]; then
        echo -e "${GREEN}Building production assets...${NC}"
        npm run build

        # Use a simple HTTP server to serve the production build
        echo -e "${GREEN}Starting production server...${NC}"
        npx serve -s dist &
        CLIENT_PID=$!
    else
        npm start &
        CLIENT_PID=$!
    fi

    cd ..
    echo -e "${GREEN}Client started with PID: ${CLIENT_PID}${NC}"
    return $CLIENT_PID
}

# Handle graceful shutdown
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"

    # Kill server process if it exists
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null
        echo -e "${GREEN}Server stopped.${NC}"
    fi

    # Kill client process if it exists
    if [ ! -z "$CLIENT_PID" ]; then
        kill $CLIENT_PID 2>/dev/null
        echo -e "${GREEN}Client stopped.${NC}"
    fi

    echo -e "${GREEN}Cleanup complete.${NC}"
    exit 0
}

# Main execution script
main() {
    # Validate mode argument
    if [ "$MODE" != "dev" ] && [ "$MODE" != "prod" ]; then
        echo -e "${RED}Error: Invalid mode. Use 'dev' or 'prod'.${NC}"
        echo -e "Usage: ./run.sh [dev|prod]"
        exit 1
    fi

    # Check requirements
    check_requirements

    # Setup environments
    setup_server
    setup_client

    # Set trap for clean shutdown
    trap cleanup SIGINT SIGTERM

    # Start components
    start_server
    SERVER_PID=$?

    start_client
    CLIENT_PID=$?

    echo -e "\n${GREEN}All components started!${NC}"
    echo -e "${BLUE}=================================${NC}"
    echo -e "${YELLOW}Server running at:${NC} http://localhost:8000"
    if [ "$MODE" = "prod" ]; then
        echo -e "${YELLOW}Client running at:${NC} http://localhost:3000"
    else
        echo -e "${YELLOW}Client running at:${NC} http://localhost:1234"
    fi
    echo -e "${BLUE}=================================${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

    # Wait for user to press Ctrl+C
    wait
}

# Run the main function
main
