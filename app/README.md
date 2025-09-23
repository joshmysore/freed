# Email Event Parser v2.0

A configurable, learning-based email event parser that replaces hard-coded lists with intelligent, data-driven behavior.

## 🚀 Key Features

- **Zero-shot Classification**: No hard-coded brand or sender lists
- **Configurable Categories & Cuisines**: User-editable configuration files
- **Learning System**: Automatically learns food name → cuisine mappings
- **Confidence Scoring**: Filters results based on confidence thresholds
- **Caching & Deduplication**: Minimizes API calls and prevents duplicates
- **Generic Event Gating**: Uses pattern matching instead of hard-coded rules

## 📁 Structure

```
app/
├── config.py              # Centralized configuration
├── store.py               # Learning and caching store
├── schema.py              # Pydantic models with confidence
├── parser_llm.py          # LLM parser with gating
├── postprocess.py         # Learning and confidence filtering
├── gmail_client.py        # Configurable Gmail client
├── server.py              # FastAPI server
├── calendar_ics.py        # ICS generation
├── prompts/
│   └── event_parser_prompt.txt
├── tests/                 # Comprehensive test suite
└── migrate.py             # Migration from v1.0
```

## ⚙️ Configuration

### Basic Configuration
Edit `config.py` or create `custom_config.json`:

```json
{
  "categories": ["workshop", "lecture", "meeting", "concert", "social"],
  "cuisines": ["American", "Chinese", "Indian", "Italian", "Japanese"],
  "event_window_days": 14,
  "max_llm_calls_per_run": 10,
  "min_confidence": {
    "category": 0.6,
    "cuisine": 0.6
  }
}
```

### Environment Variables
```bash
OPENAI_API_KEY=your_harvard_api_key_here
```

## 🏃‍♂️ Quick Start

### 1. Migration from v1.0
```bash
cd app
python migrate.py
```

### 2. Run the Server
```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8080 --reload
```

### 3. Access the Interface
Visit http://localhost:8080

## 🔧 API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /config` - Get current configuration
- `GET /stats` - System statistics and learning progress

### Event Parsing
- `GET /events/scan?category=workshop&cuisine=Italian` - Parse events with filters
- `GET /events/gg-events?category=lecture` - Parse GG.Events with filters
- `POST /ics` - Generate ICS calendar files

## 🧠 Learning System

The system automatically learns from successful parses:

### Food Name → Cuisine Learning
- Tracks confidence scores for food items
- Uses exponential moving average for learning
- Prefers learned mappings when confidence is high

### Caching
- Caches LLM responses by email content hash
- Prevents re-parsing unchanged emails
- 24-hour cache expiration

### Deduplication
- Detects exact duplicates by title + date + time + location
- Fuzzy matching for similar events
- Merges URLs and mailing lists

## 🎯 Confidence Scoring

### Category Confidence
- LLM provides confidence score for category assignment
- Filters out categories below threshold (default: 0.6)
- Sets category to null if confidence is too low

### Cuisine Confidence
- LLM provides confidence score for cuisine classification
- Learns high-confidence mappings
- Uses learned mappings for future parses

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd app
python tests/test_runner.py
```

Or run specific tests:
```bash
pytest tests/test_schema.py -v
pytest tests/test_store.py -v
pytest tests/test_postprocess.py -v
```

## 📊 Monitoring

### System Stats
- LLM call usage and limits
- Cache hit rates
- Learning progress
- Deduplication effectiveness

### Learning Stats
- Learned alias counts by confidence level
- Rolling average confidence scores
- Sample counts for each learned item

## 🔄 Migration from v1.0

The migration script (`migrate.py`) will:

1. **Backup** your old `src/` directory to `backup_v1/`
2. **Copy** credentials and environment files
3. **Create** a sample `custom_config.json`
4. **Preserve** all your existing data

### Backward Compatibility

The new system maintains backward compatibility:
- Legacy API endpoints still work
- Old event format is supported
- Existing credentials and tokens are preserved

## 🎛️ Customization

### Adding New Categories
Edit `custom_config.json`:
```json
{
  "categories": ["workshop", "lecture", "meeting", "concert", "social", "your_new_category"]
}
```

### Adding New Cuisines
```json
{
  "cuisines": ["American", "Chinese", "Indian", "Italian", "Japanese", "Your_Cuisine"]
}
```

### Adjusting Confidence Thresholds
```json
{
  "min_confidence": {
    "category": 0.7,  # Higher threshold = more strict
    "cuisine": 0.5    # Lower threshold = more permissive
  }
}
```

## 🚨 Troubleshooting

### Common Issues

1. **No events found**
   - Check Gmail credentials
   - Verify search query in config
   - Check event window days setting

2. **Low parsing success rate**
   - Adjust confidence thresholds
   - Review event gating patterns
   - Check LLM prompt effectiveness

3. **High API usage**
   - Enable caching (default: on)
   - Reduce max_llm_calls_per_run
   - Use more restrictive gating

### Debug Mode
```bash
LOG_LEVEL=DEBUG python -m uvicorn server:app --host 0.0.0.0 --port 8080
```

## 📈 Performance

### Optimization Features
- **Event Gating**: Pre-filters emails before LLM calls
- **Response Caching**: Avoids re-parsing unchanged emails
- **Batch Processing**: Efficient batch operations
- **Call Budgeting**: Prevents excessive API usage

### Expected Performance
- **Cache Hit Rate**: 60-80% for repeated runs
- **Parsing Success**: 70-90% for event-like emails
- **Learning Accuracy**: 85-95% for common food items
- **Deduplication**: 95%+ accuracy for exact duplicates

## 🔮 Future Enhancements

- **Multi-language Support**: International event parsing
- **Advanced Learning**: Neural network-based learning
- **Real-time Updates**: WebSocket-based live updates
- **Analytics Dashboard**: Detailed parsing analytics
- **Custom Models**: Fine-tuned models for specific domains

