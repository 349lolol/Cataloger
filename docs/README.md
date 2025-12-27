# CatalogAI Documentation

## 📚 Documentation Structure

### Planning Documents
Located in `docs/planning/`

- **[PROJECT_STATUS.md](planning/PROJECT_STATUS.md)** - Detailed implementation status, phases completed, next steps
- **[IMPLEMENTATION_SUMMARY.md](planning/IMPLEMENTATION_SUMMARY.md)** - High-level project summary, tech decisions, competitive analysis
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Complete file organization and directory structure

### User Guides
Located in `docs/guides/`

- **[USAGE_EXAMPLES.md](guides/USAGE_EXAMPLES.md)** - API usage examples, common workflows, code samples
- **[MCP_INTEGRATION.md](guides/MCP_INTEGRATION.md)** - Complete guide to MCP code execution setup

### API Reference
Located in `docs/api/`

- **[API_REFERENCE.md](api/API_REFERENCE.md)** - Complete API endpoint documentation *(TODO)*
- **[AUTHENTICATION.md](api/AUTHENTICATION.md)** - Auth setup and JWT usage *(TODO)*

---

## 🚀 Quick Links

### Getting Started
1. [Main README](../README.md) - Start here for setup
2. [Usage Examples](guides/USAGE_EXAMPLES.md) - See how to use the API
3. [Project Status](planning/PROJECT_STATUS.md) - What's implemented

### Advanced Features
- [MCP Integration](guides/MCP_INTEGRATION.md) - Connect with Claude Desktop
- [Deployment Guide](../README.md#deployment-options) - Deploy to AWS

### Development
- [Database Schema](../supabase/migrations/) - SQL migration files
- [Python SDK](../catalogai_sdk/) - Client library source code
- [MCP Server](../catalogai_mcp/) - Code execution server

---

## 📖 Documentation by Role

### For Users
- How to search the catalog → [Usage Examples](guides/USAGE_EXAMPLES.md#1-search-for-an-item)
- How to request new items → [Usage Examples](guides/USAGE_EXAMPLES.md#2-request-new-item-when-search-fails)
- Using with Claude → [MCP Integration](guides/MCP_INTEGRATION.md)

### For Developers
- Setting up locally → [Main README](../README.md#quick-start)
- API documentation → [Usage Examples](guides/USAGE_EXAMPLES.md)
- Adding features → [Project Status](planning/PROJECT_STATUS.md#next-steps)

### For Admins
- Deployment guide → [Main README](../README.md#deployment-options)
- Database migrations → [Project Status](planning/PROJECT_STATUS.md#phase-2-database-supabasepostgresql)
- Security setup → [Main README](../README.md#security)

---

## 🗂️ File Organization

```
docs/
├── README.md                      # This file
├── planning/                      # Project planning & status
│   ├── PROJECT_STATUS.md          # Detailed implementation status
│   └── IMPLEMENTATION_SUMMARY.md  # High-level summary
├── guides/                        # User guides & tutorials
│   ├── USAGE_EXAMPLES.md          # API usage examples
│   └── MCP_INTEGRATION.md         # MCP setup guide
└── api/                           # API documentation (future)
    ├── API_REFERENCE.md
    └── AUTHENTICATION.md
```

---

## 🔄 Documentation Updates

When adding new features:
1. Update [PROJECT_STATUS.md](planning/PROJECT_STATUS.md) with implementation details
2. Add usage examples to [USAGE_EXAMPLES.md](guides/USAGE_EXAMPLES.md)
3. Update API reference if new endpoints added
4. Update [Main README](../README.md) if setup process changes

---

## 💡 Contributing

See the main [README](../README.md) for contribution guidelines.
