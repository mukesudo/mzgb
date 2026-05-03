#!/bin/bash

# LogSnap MVP Demo Script
# This script demonstrates the core functionality of LogSnap

echo "🚀 LogSnap MVP Demo"
echo "=================="
echo

# Create a sample log file for demonstration
echo "📝 Creating sample log file..."
cat > sample_app.log << 'EOF'
2024-01-15 14:00:01 INFO Starting application server on port 8080
2024-01-15 14:00:02 INFO Database connection established
2024-01-15 14:00:03 WARN High memory usage detected: 85%
2024-01-15 14:00:04 ERROR Failed to connect to external API: timeout
2024-01-15 14:00:05 INFO User login: user123 from 192.168.1.100
2024-01-15 14:00:06 ERROR Database query failed: connection refused
2024-01-15 14:00:07 INFO Processing batch job: 1000 records
2024-01-15 14:00:08 WARN Rate limit approaching: 950/1000 requests
2024-01-15 14:00:09 ERROR File not found: /var/log/old.log
2024-01-15 14:00:10 INFO Application shutdown complete
EOF

echo "✅ Sample log file created (10 lines)"
echo

# Demo 1: Basic filtering by log level
echo "🔍 Demo 1: Filter by ERROR level"
echo "--------------------------------"
python3 -m logsnap --level ERROR sample_app.log
echo

# Demo 2: Pattern matching
echo "🔍 Demo 2: Search for 'connection' pattern"
echo "-----------------------------------------"
python3 -m logsnap --pattern "connection" sample_app.log
echo

# Demo 3: Context around matches
echo "🔍 Demo 3: Find ERROR with 2 lines context"
echo "----------------------------------------"
python3 -m logsnap --level ERROR --context 2 sample_app.log
echo

# Demo 4: Summary statistics
echo "📊 Demo 4: Log summary statistics"
echo "-------------------------------"
python3 -m logsnap --summary sample_app.log
echo

# Demo 5: Multiple filters
echo "🔍 Demo 5: Multiple filters (ERROR or WARN)"
echo "-----------------------------------------"
python3 -m logsnap --level ERROR --level WARN sample_app.log
echo

# Clean up
echo "🧹 Cleaning up..."
rm sample_app.log
echo "✅ Demo complete!"
echo

echo "🎯 LogSnap MVP Features Demonstrated:"
echo "  ✓ Log level filtering"
echo "  ✓ Pattern matching"
echo "  ✓ Context awareness"
echo "  ✓ Summary statistics"
echo "  ✓ Multiple filters"
echo "  ✓ Memory-efficient streaming"
echo

echo "🤖 Autonomous Agents:"
echo "  Run 'sh start_agents.sh start' to launch AI-powered agents"
echo "  Agents can automatically implement features using LLMs"
echo

echo "📚 More info: https://github.com/mukesudo/logsnap"
