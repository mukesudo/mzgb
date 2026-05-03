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

## � Experimental Features

LogSnap includes an experimental autonomous agent system for AI-powered development. This is a research project exploring how AI agents can automatically implement features. The core LogSnap CLI works perfectly without these agents - they're just for experimentation.

```bash
# Experimental: Start autonomous agents (optional)
sh start_agents.sh start
```

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
├── tests/             # Test suite
├── examples/          # Example log files
├── demo.sh            # Demo script
└── README.md

# Experimental (optional)
├── agents/            # Autonomous agents (experimental)
├── tasks/             # Task queue system (experimental)
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

**For Experimental Features (optional):**
- Matrix server for autonomous agents
- API keys for LLM providers (Groq, Gemini)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ for developers who deal with massive log files daily
- Inspired by the need for faster log analysis tools
- Thanks to all contributors who help improve LogSnap

---

**Made with ❤️ by [Mukhtar Saeed](https://github.com/mukesudo)**

If you find LogSnap useful, please give it a ⭐ on GitHub!

---

## 🎯 MVP Status

✅ **Core CLI Functionality**: Fully working log filtering and analysis  
✅ **Memory Efficient**: Processes large files without loading everything into memory  
✅ **Comprehensive Features**: Log levels, patterns, time ranges, context, summaries  
✅ **Production Ready**: Tested with 84.91% coverage and automated quality checks  

The MVP provides a complete, professional log analysis tool for developers and DevOps engineers.
