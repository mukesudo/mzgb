# LogSnap 🚀

**Fast, intelligent log filtering for very large log files**

LogSnap is a powerful command-line tool that helps you quickly filter and analyze massive log files without loading everything into memory. Perfect for developers, DevOps engineers, and system administrators who need to find critical information in logs quickly.

## ✨ Features

- **🔍 Smart Filtering**: Filter by log level, patterns, or time ranges
- **⚡ Lightning Fast**: Processes gigabytes of logs in seconds
- **💾 Memory Efficient**: Streams data without loading entire files
- **🎯 Context Awareness**: Show lines before and after matches
- **📊 Summary Mode**: Get statistics and insights about your logs
- **🔄 Real-time Monitoring**: Follow logs as they're written (like `tail -f`)
- **🤖 Autonomous Agents**: AI-powered agents that can implement features automatically

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/mukesudo/logsnap.git
cd logsnap

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Basic Usage

```bash
# Filter by log level
logsnap --level ERROR app.log

# Search for patterns with context
logsnap --pattern "timeout" --context 3 app.log

# Filter by time range
logsnap --from "2024-01-15 14:00" --to "2024-01-15 15:00" app.log

# Get a summary of your logs
logsnap --summary app.log

# Follow logs in real-time
logsnap --follow --level ERROR app.log

# Pipe data directly
cat app.log | logsnap --pattern "connection refused"
```

## 🤖 Autonomous Agents

LogSnap includes a revolutionary autonomous agent system that can implement features automatically using AI. The agents work on a task queue system and communicate via Matrix chat.

### Starting the Agents

```bash
# Start all autonomous agents
sh start_agents.sh start

# Stop all agents
sh start_agents.sh stop

# Check agent status
sh start_agents.sh status
```

### Available Agents

- **Biruk** - Backend specialist (parser.py, filters.py)
- **Liya** - CLI expert (cli.py, command-line interface)
- **Tigist** - Features developer (new features, enhancements)
- **Natnael** - Infrastructure engineer (build, CI/CD, deployment)
- **Abel** - Project manager (coordination, testing)
- **Dawit** - Code quality specialist (linting, formatting)
- **Endalk** - Documentation writer (README, docs)
- **Selam** - Integration tester (E2E tests)

## 📖 Examples

### Find All Errors with Context
```bash
logsnap --level ERROR --context 5 production.log
```

### Monitor Application in Real-time
```bash
logsnap --follow --level ERROR,WARN app.log
```

### Analyze Time-based Issues
```bash
logsnap --from "2024-01-15 14:00:00" --to "2024-01-15 14:30:00" --pattern "database" app.log
```

### Get Log Statistics
```bash
logsnap --summary access.log
```

## 🏗️ Project Structure

```
logsnap/
├── logsnap/           # Core package
│   ├── __init__.py
│   ├── cli.py         # Command-line interface
│   ├── parser.py      # Log parsing logic
│   ├── filters.py     # Filtering engine
│   └── renderer.py    # Output formatting
├── agents/            # Autonomous agents
│   ├── biruk.py       # Backend specialist
│   ├── liya.py        # CLI expert
│   ├── tigist.py      # Features developer
│   ├── natnael.py     # Infrastructure engineer
│   └── ...           # More agents
├── tasks/             # Task queue system
│   ├── QUEUE.json     # Task definitions
│   └── queue_manager.py
├── tests/             # Test suite
├── examples/          # Example log files
└── README.md
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=logsnap

# Run specific test
python -m pytest tests/test_parser.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Requirements

- Python 3.8+
- No external dependencies for core functionality
- Matrix server for autonomous agents (optional)
- API keys for LLM providers (Groq, Gemini)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ for developers who deal with massive log files daily
- Inspired by the need for faster log analysis tools
- Revolutionary autonomous agent system powered by AI
- Thanks to all contributors who help improve LogSnap

---

**Made with ❤️ by [Mukhtar Saeed](https://github.com/mukesudo)**

If you find LogSnap useful, please give it a ⭐ on GitHub!

---

## 🎯 MVP Status

✅ **Core CLI Functionality**: Fully working log filtering and analysis  
✅ **Autonomous Agent Framework**: Complete agent system with Matrix integration  
✅ **Task Queue System**: Automated task distribution and tracking  
✅ **LLM Integration**: AI-powered code generation and implementation  
🔄 **Agent Debugging**: Currently fine-tuning autonomous agent execution  

The MVP demonstrates both traditional CLI usage and cutting-edge autonomous development!
