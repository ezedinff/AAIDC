# AI Video Generator

A comprehensive multi-agent system for automated video content creation using AI. Generate high-quality videos with synchronized audio narration from simple text descriptions.

![Workflow](https://github.com/ezedinff/AAIDC/blob/main/project-2/backend/graph.png?raw=true)

## 🎬 Demo Video

Watch the AI Video Generator in action:

[![AI Video Generator Demo](https://img.youtube.com/vi/Mu-_XU85XgY/0.jpg)](https://www.youtube.com/watch?v=Mu-_XU85XgY)

*This demo shows the complete workflow from text input to final video generation using our multi-agent system.*

## 🚀 Quick Start with Docker Compose

### Prerequisites

- **Docker Engine** 20.10+ 
- **Docker Compose** 2.0+
- **8GB RAM** minimum (8GB recommended)
- **OpenAI API Key** with GPT-4 access

### 1. Clone the Repository

```bash
git clone https://github.com/ezedinff/AAIDC.git
cd AAIDC/project-2
```

### 2. Environment Setup

Create the required environment file:

```bash
# Copy the example environment file
cp backend/env.example backend/.env

# Add your OpenAI API key
echo "OPENAI_API_KEY=your_openai_api_key_here" >> backend/.env
```

**Required Environment Variables:**
```env
OPENAI_API_KEY=your_openai_api_key_here
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=sqlite:///data/video_generator.db
```

### 3. Create Required Directories

```bash
# Create directories for persistent data
mkdir -p data outputs temp
```

### 4. Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up --build -d
```

### 5. Access the Application

- **Frontend (Web Interface)**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api/docs

## 🎯 How It Works

The system employs 5 specialized AI agents working together:

1. **Scene Generator Agent** - Transforms your description into structured video scenes
2. **Database Logger Agent** - Tracks all progress and maintains audit trails
3. **Scene Critic Agent** - Reviews and improves scene quality
4. **Audio Agent** - Generates synchronized narration
5. **Video Agent** - Combines everything into the final MP4

## 📱 Usage Examples

### Web Interface
1. Open http://localhost:3000
2. Enter a description like "Create a video about the history of coffee"
3. Watch real-time progress as AI generates your video
4. Download the final MP4 when complete

### API Usage

**Create a new video:**
```bash
curl -X POST http://localhost:5000/api/videos \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Coffee History",
    "description": "Educational video about coffee origins",
    "user_input": "Create a 3-minute video about how coffee was discovered in Ethiopia and spread worldwide"
  }'
```

**Monitor progress:**
```bash
# Get video status
curl http://localhost:5000/api/videos/{video_id}

# Watch real-time progress
curl -N http://localhost:5000/api/videos/{video_id}/events
```

## 🛠️ Docker Compose Commands

### Basic Operations
```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# Rebuild and start
docker-compose up --build

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Development Commands
```bash
# Restart specific service
docker-compose restart backend

# Execute commands in running container
docker-compose exec backend python -c "print('Hello from backend')"
docker-compose exec frontend npm run dev

# Check service status
docker-compose ps

# Remove all containers and volumes
docker-compose down -v
```

### Troubleshooting
```bash
# Clean rebuild (removes cache)
docker-compose build --no-cache

# Check resource usage
docker-compose top

# Access container shell
docker-compose exec backend bash
docker-compose exec frontend bash

# View container resource stats
docker stats
```

## 📁 Project Structure

```
project-2/
├── backend/                 # Flask API backend
│   ├── agents/             # AI agent implementations
│   ├── config/             # Configuration files
│   ├── tools/              # Database and utility tools
│   ├── .env                # Environment variables
│   └── Dockerfile          # Backend Docker configuration
├── frontend/               # Next.js web interface
│   ├── app/                # Next.js app directory
│   ├── components/         # React components
│   └── Dockerfile          # Frontend Docker configuration
├── data/                   # Persistent database storage
├── outputs/                # Generated video files
├── temp/                   # Temporary processing files
├── docker-compose.yml      # Docker Compose configuration
├── LICENSE                 # MIT License
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | **Required** |
| `FLASK_ENV` | Flask environment | `development` |
| `FLASK_DEBUG` | Enable Flask debug mode | `1` |
| `DATABASE_URL` | Database connection string | `sqlite:///data/video_generator.db` |
| `NEXT_PUBLIC_API_URL` | Frontend API URL | `http://localhost:5000` |

### Volume Mounts

The Docker Compose setup includes several volume mounts:

- `./backend:/app` - Live code reloading for backend
- `./frontend:/app` - Live code reloading for frontend  
- `./outputs:/app/outputs` - Persistent video storage
- `./data:/app/data` - Database persistence
- `./temp:/app/temp` - Temporary file storage

## 🎬 Example Video Prompts

Try these example prompts to test the system:

- **Educational**: "Create a video explaining how photosynthesis works in plants"
- **Historical**: "Tell the story of the first moon landing in 1969"
- **Tutorial**: "Show how to make homemade pasta step by step"
- **Science**: "Explain the water cycle and its importance to Earth's ecosystem"
- **Technology**: "Describe how the internet works and data travels across networks"

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Check what's using the ports
lsof -i :3000
lsof -i :5000

# Kill processes if needed
sudo kill -9 $(lsof -t -i:3000)
sudo kill -9 $(lsof -t -i:5000)
```

**Docker Build Fails:**
```bash
# Clean Docker system
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

**Permission Issues:**
```bash
# Fix directory permissions
sudo chown -R $USER:$USER data outputs temp
chmod 755 data outputs temp
```

**API Rate Limits:**
- Check your OpenAI API usage and limits
- Ensure your API key has sufficient credits
- Monitor rate limiting in the backend logs

### Log Analysis
```bash
# Backend logs for API issues
docker-compose logs backend | grep ERROR

# Frontend logs for UI issues  
docker-compose logs frontend | grep error

# Database connection issues
docker-compose logs backend | grep database
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test with Docker Compose
4. Commit your changes: `git commit -am 'Add new feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/ezedinff/AAIDC/issues)
- **Discussions**: [Community forum](https://github.com/ezedinff/AAIDC/discussions)
- **Documentation**: [Full academic paper](pub.md)

## 🔗 Links

- **Repository**: https://github.com/ezedinff/AAIDC/tree/main/project-2
- **Demo**: http://localhost:3000 (after setup)
- **API Docs**: http://localhost:5000/api/docs (after setup)