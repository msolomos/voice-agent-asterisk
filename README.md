# Voice Agent - AI-Powered Voice Assistant

An integrated voice assistant system that combines Asterisk PBX with AI to provide intelligent voice interactions. The system uses OpenAI for natural language processing and text-to-speech functionality.

## 🚀 Features

- **AI-Powered Voice Recognition**: Uses OpenAI for processing and understanding voice commands
- **Text-to-Speech**: Text-to-speech conversion with multi-language support
- **Asterisk Integration**: Full integration with Asterisk PBX for telephone calls
- **RESTful API**: FastAPI backend for easy extension and integration
- **Docker Support**: Fully containerized for easy installation and deployment
- **Health Monitoring**: Built-in health checks for monitoring

## 🏗️ Architecture

The system consists of the following components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Asterisk PBX  │───▶│  Voice Agent    │───▶│   OpenAI API    │
│                 │    │   (Python)      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  AGI Scripts    │    │   FastAPI       │
│                 │    │   Server        │
└─────────────────┘    └─────────────────┘
```

### Main Components:

1. **voice_agent.py**: The main FastAPI application
2. **voice_bridge_fixed.agi**: AGI script for communication with the voice agent
3. **voice_route.agi**: AGI script for call routing
4. **Asterisk Dialplan**: Call flow orchestration

## 📋 Prerequisites

- Docker & Docker Compose
- Asterisk PBX (installed and configured)
- OpenAI API Key
- Python 3.11+ (for local development)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/msolomos/voice-agent-asterisk
cd voice-agent-asterisk
```

### 2. Environment Setup

Create a `.env` file in the root directory:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Application Configuration  
APP_HOST=0.0.0.0
APP_PORT=5000
DEBUG=false

# Voice Configuration
DEFAULT_LANGUAGE=en
TTS_ENGINE=google
VOICE_TIMEOUT=10
MAX_RECORDING_TIME=30

# Asterisk Configuration
ASTERISK_AGI_PATH=/var/lib/asterisk/agi-bin/
TEMP_AUDIO_PATH=/tmp/
```

### 3. Docker Deployment

```bash
# Build and start the container
docker-compose up -d

# Check logs
docker-compose logs -f voice-agent

# Check health status
curl http://localhost:5000/health
```

### 4. Asterisk Configuration

Add the following dialplan to `/etc/asterisk/extensions.conf`:

```ini
[voice-agent-test]
exten => 997,1,Answer()
exten => 997,2,AGI(googletts.agi,"Hello, how can I help you?",en)
exten => 997,3,Wait(1)
exten => 997,4,Record(/tmp/voice_input_${UNIQUEID}.wav,3,10,q)
exten => 997,5,AGI(voice_bridge_fixed.agi,${UNIQUEID})
exten => 997,6,System(cp /tmp/voice_response_${UNIQUEID}.wav /tmp/final_response.wav)
exten => 997,7,Wait(1)
exten => 997,8,Playback(/tmp/final_response)
exten => 997,9,GotoIf($["${STAT(e,/tmp/final_response.wav)}" != "1"]?998,1)
exten => 997,10,AGI(voice_route.agi,${UNIQUEID})
exten => 997,11,Goto(ext-local,${ROUTE_EXT},1)
exten => 997,12,Hangup()
```

Copy AGI scripts:

```bash
# Copy AGI scripts to Asterisk directory
sudo cp voice_bridge_fixed.agi /var/lib/asterisk/agi-bin/
sudo cp voice_route.agi /var/lib/asterisk/agi-bin/
sudo chmod +x /var/lib/asterisk/agi-bin/*.agi

# Restart Asterisk
sudo systemctl restart asterisk
```

## 🔧 Usage

### Phone Call

1. Call extension `997`
2. Listen to the welcome message
3. Speak when recording starts
4. The system will process your voice and respond

### API Endpoints

```bash
# Health Check
GET http://localhost:5000/health

# Process Voice (for manual testing)
POST http://localhost:5000/process-voice
Content-Type: multipart/form-data
{
  "audio_file": "voice_recording.wav",
  "unique_id": "test123"
}
```

### Testing

```bash
# Check container status
docker-compose ps

# Live logs
docker-compose logs -f

# Check API health
curl -f http://localhost:5000/health || echo "Service not healthy"
```

## 📁 Project Structure

```
voice-agent/
├── voice_agent.py            # Main FastAPI application
├── voice_bridge_fixed.agi    # AGI bridge script
├── voice_route.agi           # AGI routing script
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker build configuration
├── docker-compose.yml        # Docker orchestration
├── .env.example              # Environment variables template
├── README.md                 # This file
├── logs/                     # Application logs
├── temp/                     # Temporary audio files
└── scripts/                  # Additional utility scripts
```

## 🔍 Troubleshooting

### Common Issues

1. **Container won't start**:
   ```bash
   # Check logs for errors
   docker-compose logs voice-agent
   
   # Rebuild container
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Audio processing errors**:
   - Ensure OpenAI API key is correct
   - Check permissions on `/tmp/` directory
   - Verify audio files are in correct format

3. **AGI Scripts not executing**:
   ```bash
   # Check permissions
   sudo chmod +x /var/lib/asterisk/agi-bin/*.agi
   
   # Check Asterisk logs
   sudo tail -f /var/log/asterisk/full
   ```

4. **API connectivity issues**:
   ```bash
   # Test network connectivity
   docker exec voice-agent curl -I http://localhost:5000/health
   
   # Check port binding
   netstat -tulpn | grep :5000
   ```

### Debug Mode

For more debugging information:

```bash
# Enable debug mode
echo "DEBUG=true" >> .env
docker-compose restart voice-agent

# Monitor detailed logs
docker-compose logs -f voice-agent
```

## 🚀 Production Deployment

### Security Considerations

1. **Environment Variables**: Never commit `.env` file with real API keys
2. **Network Security**: Use reverse proxy (nginx) for HTTPS
3. **Access Control**: Restrict API access
4. **Monitoring**: Set up monitoring for production use

### Production Docker Compose

```yaml
version: '3.8'
services:
  voice-agent:
    build: .
    restart: always
    environment:
      - PYTHONUNBUFFERED=1
    env_file:
      - .env.production
    volumes:
      - ./logs:/app/logs
      - ./temp:/app/temp
    networks:
      - voice-network
      
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - voice-agent
    networks:
      - voice-network

networks:
  voice-network:
    driver: bridge
```

### Environment Variables

Create a `.env.production` file for production:

```bash
# Production OpenAI Configuration
OPENAI_API_KEY=your_production_openai_api_key

# Production Application Configuration
APP_HOST=0.0.0.0
APP_PORT=5000
DEBUG=false

# Production Voice Configuration
DEFAULT_LANGUAGE=en
TTS_ENGINE=google
VOICE_TIMEOUT=10
MAX_RECORDING_TIME=30

# Production Asterisk Configuration
ASTERISK_AGI_PATH=/var/lib/asterisk/agi-bin/
TEMP_AUDIO_PATH=/tmp/

# Additional production settings
LOG_LEVEL=INFO
MAX_CONCURRENT_CALLS=10
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

## 🌐 Multi-Language Support

The system supports multiple languages for both speech recognition and text-to-speech:

### Supported Languages

- **English (en)**: Default language
- **Greek (el)**: Ελληνική υποστήριξη
- **Spanish (es)**: Soporte en español
- **French (fr)**: Support français
- **German (de)**: Deutsche Unterstützung

### Language Configuration

```bash
# Set default language in .env
DEFAULT_LANGUAGE=en

# Or configure per-call in dialplan
exten => 997,2,AGI(googletts.agi,"Hello, how can I help you?",en)
exten => 998,2,AGI(googletts.agi,"Γειά σας, πως μπορώ να βοηθήσω;",el)
```

## 📊 Monitoring & Logging

### Health Checks

The application includes comprehensive health monitoring:

```bash
# Basic health check
curl http://localhost:5000/health

# Detailed health information
curl http://localhost:5000/health/detailed
```

### Logging

Logs are stored in the `./logs/` directory:

- `voice_agent.log`: Main application logs
- `error.log`: Error-specific logs
- `access.log`: API access logs

### Monitoring Setup

For production monitoring, consider integrating:

- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **ELK Stack**: Log aggregation
- **Sentry**: Error tracking

## 🔧 API Reference

### Endpoints

#### Health Check
```http
GET /health
```
Returns service health status.

#### Process Voice
```http
POST /process-voice
Content-Type: multipart/form-data
```

**Parameters:**
- `audio_file` (file): Audio file in WAV format
- `unique_id` (string): Unique identifier for the call
- `language` (string, optional): Language code (default: en)

**Response:**
```json
{
  "status": "success",
  "unique_id": "test123",
  "response_file": "/tmp/voice_response_test123.wav",
  "transcript": "Hello, how are you?",
  "response_text": "I'm doing well, thank you for asking!"
}
```

#### Get Call Status
```http
GET /call-status/{unique_id}
```
Returns the status of a specific call.

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/msolomos/voice-agent-asterisk
cd voice-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally
python voice_agent.py
```

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings for functions and classes
- Include type hints where appropriate

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support & Community

For support and questions:

- **Issues**: [GitHub Issues](https://github.com/msolomos/voice-agent-asterisk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/msolomos/voice-agent-asterisk/discussions)
- **Email**: msolomos2@gmail.com

### Community Guidelines

- Be respectful and inclusive
- Provide detailed information when reporting issues
- Search existing issues before creating new ones
- Use clear and descriptive titles

## 🚧 Roadmap

### Upcoming Features

- [ ] **Multi-tenant Support**: Support for multiple organizations
- [ ] **Advanced Analytics**: Call analytics and reporting
- [ ] **Voice Biometrics**: Speaker identification and verification
- [ ] **Webhook Support**: Integration with external systems
- [ ] **GUI Dashboard**: Web-based management interface
- [ ] **Load Balancing**: Support for multiple voice agent instances
- [ ] **Custom Voice Models**: Integration with custom TTS models

### Version History

- **v1.0.0**: Initial release with basic voice processing
- **v1.1.0**: Added multi-language support
- **v1.2.0**: Docker containerization
- **v1.3.0**: Health monitoring and logging improvements

## 🙏 Acknowledgments

- [OpenAI](https://openai.com/) for the API
- [Asterisk](https://www.asterisk.org/) for PBX functionality
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- The open source community for tools and libraries

## 📈 Performance

### System Requirements

**Minimum:**
- 2 CPU cores
- 4GB RAM
- 10GB storage
- Docker support

**Recommended:**
- 4+ CPU cores
- 8GB+ RAM
- 50GB+ storage
- SSD storage

### Performance Metrics

- **Response Time**: < 2 seconds average
- **Concurrent Calls**: Up to 10 simultaneous calls
- **Uptime**: 99.9% availability target
- **Audio Quality**: 16kHz, 16-bit WAV processing

---

**⭐ If you find this project useful, please give it a star!**

**🔗 Connect with us:**
- [LinkedIn](https://linkedin.com/in/gerasimos-solomos)
- [Website](https://f2d.gr)